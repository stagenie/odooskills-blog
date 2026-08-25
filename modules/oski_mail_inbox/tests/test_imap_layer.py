from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


class FakeImapServer:
    """Double IMAP paramétrable. Enregistre chaque commande reçue pour que
    les tests puissent prouver ce qui n'a PAS été envoyé."""

    def __init__(self, folders=None, capabilities=('IMAP4REV1',), uids_found=(7,)):
        self.folders = folders if folders is not None else [
            (br'(\HasNoChildren \Trash) "." "INBOX.Trash"'),
            (br'(\HasNoChildren \Junk) "." "INBOX.Junk"'),
            (br'(\HasNoChildren) "." "INBOX"'),
        ]
        self.capabilities = capabilities
        self.uids_found = list(uids_found)
        self.commands = []
        self.selected = None
        self.copied_to = []
        self.moved_to = []
        self.flags_set = []

    # -- commandes utilisées par la couche --------------------------------
    def list(self):
        self.commands.append(('LIST',))
        return 'OK', list(self.folders)

    def select(self, mailbox, readonly=False):
        self.commands.append(('SELECT', mailbox, readonly))
        known = [b'INBOX'] + [f.rsplit(b'"', 2)[-2] for f in self.folders]
        name = mailbox.strip('"').encode()
        if name not in known:
            return 'NO', [b'no such mailbox']
        self.selected = mailbox
        return 'OK', [b'1']

    def uid(self, command, *args):
        self.commands.append((command.upper(),) + args)
        upper = command.upper()
        if upper == 'SEARCH':
            payload = ' '.join(str(u) for u in self.uids_found).encode()
            return 'OK', [payload]
        if upper == 'MOVE':
            if 'MOVE' not in self.capabilities:
                return 'NO', [b'command not supported']
            self.moved_to.append(args[1])
            return 'OK', [b'done']
        if upper == 'COPY':
            self.copied_to.append(args[1])
            return 'OK', [b'done']
        if upper == 'STORE':
            self.flags_set.append(args)
            return 'OK', [b'done']
        if upper == 'EXPUNGE':
            if 'UIDPLUS' not in self.capabilities:
                return 'NO', [b'command not supported']
            return 'OK', [b'done']
        raise AssertionError('commande inattendue %s' % command)

    def expunge(self):
        raise AssertionError(
            "EXPUNGE nu appelé : il purgerait les messages marqués par un autre client")

    def logout(self):
        pass


@tagged('post_install', '-at_install')
class TestImapLayer(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.box = cls.env['oski.mailbox'].create({
            'name': 'Odooers', 'email': 'tests-imap@odooskills.example',
            'imap_host': 'imap.test.local', 'imap_user': 'u',
            'imap_password': 'fake-test-password',
        })

    # -- résolution des dossiers -----------------------------------------
    def test_resolve_uses_special_use_flag(self):
        fake = FakeImapServer()
        self.assertEqual(self.box._imap_resolve_folder(fake, 'trash'), 'INBOX.Trash')
        self.assertEqual(self.box._imap_resolve_folder(fake, 'junk'), 'INBOX.Junk')

    def test_resolve_memorises_result(self):
        fake = FakeImapServer()
        self.box._imap_resolve_folder(fake, 'trash')
        self.assertEqual(self.box.trash_folder, 'INBOX.Trash',
                         "le dossier trouvé doit être mémorisé pour ne pas refaire un LIST")

    def test_configured_folder_wins_without_list(self):
        self.box.trash_folder = 'Poubelle'
        fake = FakeImapServer()
        self.assertEqual(self.box._imap_resolve_folder(fake, 'trash'), 'Poubelle')
        self.assertNotIn(('LIST',), fake.commands,
                         "un dossier saisi à la main rend le LIST inutile")

    def test_resolve_falls_back_on_common_names(self):
        # serveur sans SPECIAL-USE : les flags n'apparaissent pas dans LIST
        fake = FakeImapServer(folders=[b'(\\HasNoChildren) "." "Trash"',
                                       b'(\\HasNoChildren) "." "INBOX"'])
        self.assertEqual(self.box._imap_resolve_folder(fake, 'trash'), 'Trash')

    def test_resolve_raises_when_nothing_found(self):
        fake = FakeImapServer(folders=[b'(\\HasNoChildren) "." "INBOX"'])
        with self.assertRaises(UserError):
            self.box._imap_resolve_folder(fake, 'junk')

    # -- déplacement ------------------------------------------------------
    def test_move_uses_move_when_advertised(self):
        fake = FakeImapServer(capabilities=('IMAP4REV1', 'MOVE'))
        result = self.box._imap_move_message(fake, '<abc@example.com>', 'INBOX.Trash')
        self.assertEqual(result, 'moved')
        self.assertEqual(fake.moved_to, ['"INBOX.Trash"'])
        self.assertEqual(fake.copied_to, [], "MOVE disponible : pas de COPY de repli")

    def test_move_falls_back_to_copy_and_uid_expunge(self):
        fake = FakeImapServer(capabilities=('IMAP4REV1', 'UIDPLUS'))
        result = self.box._imap_move_message(fake, '<abc@example.com>', 'INBOX.Trash')
        self.assertEqual(result, 'moved')
        self.assertEqual(fake.copied_to, ['"INBOX.Trash"'])
        expunges = [c for c in fake.commands if c[0] == 'EXPUNGE']
        self.assertEqual(len(expunges), 1)
        self.assertEqual(expunges[0][1], b'7',
                         "UID EXPUNGE doit nommer l'UID, sinon il purge tout le dossier")

    def test_move_without_uidplus_does_not_purge(self):
        fake = FakeImapServer(capabilities=('IMAP4REV1',))
        result = self.box._imap_move_message(fake, '<abc@example.com>', 'INBOX.Trash')
        self.assertEqual(result, 'copied_not_purged')
        self.assertEqual(fake.copied_to, ['"INBOX.Trash"'])
        self.assertTrue(fake.flags_set, "le message doit au moins être marqué \\Deleted")

    def test_missing_message_is_a_success(self):
        fake = FakeImapServer(uids_found=())
        result = self.box._imap_move_message(fake, '<nulle-part@example.com>', 'INBOX.Trash')
        self.assertEqual(result, 'absent',
                         "l'état visé est 'plus dans INBOX' : déjà absent = objectif atteint")

    def test_never_calls_naked_expunge(self):
        # les quatre chemins de déplacement, sur le même double
        for caps in (('IMAP4REV1', 'MOVE'), ('IMAP4REV1', 'UIDPLUS'),
                     ('IMAP4REV1',), ('IMAP4REV1', 'MOVE', 'UIDPLUS')):
            fake = FakeImapServer(capabilities=caps)
            self.box._imap_move_message(fake, '<abc@example.com>', 'INBOX.Trash')
            for command in fake.commands:
                if command[0] == 'EXPUNGE':
                    self.assertEqual(len(command), 2,
                                     "EXPUNGE sans UID purgerait le courrier d'autrui")

    def test_search_uses_header_not_uid(self):
        fake = FakeImapServer(capabilities=('IMAP4REV1', 'MOVE'))
        self.box._imap_move_message(fake, '<abc@example.com>', 'INBOX.Trash')
        search = next(c for c in fake.commands if c[0] == 'SEARCH')
        self.assertIn('HEADER', search)
        self.assertIn('Message-ID', search)
