from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


class FakeImapServer:
    """Double IMAP paramétrable. Enregistre chaque commande reçue pour que
    les tests puissent prouver ce qui n'a PAS été envoyé.

    Toute commande UID exige un SELECT préalable (comme un vrai serveur, qui
    refuse SEARCH/COPY/STORE/EXPUNGE/MOVE en dehors de l'état SELECTED) :
    l'appeler sans avoir sélectionné une boîte lève AssertionError."""

    def __init__(self, folders=None, capabilities=('IMAP4REV1',), uids_found=(7,),
                 message_ids=None, search_status='OK', fetch_status='OK',
                 copy_status='OK', store_status='OK', move_status='OK',
                 move_statuses=None, deny_inbox_select=False):
        self.folders = folders if folders is not None else [
            (br'(\HasNoChildren \Trash) "." "INBOX.Trash"'),
            (br'(\HasNoChildren \Junk) "." "INBOX.Junk"'),
            (br'(\HasNoChildren) "." "INBOX"'),
        ]
        self.capabilities = capabilities
        self.uids_found = list(uids_found)
        # uid (bytes, ex. b'7') -> Message-ID renvoyé par un FETCH d'en-tête.
        # Par défaut (non listé ici), un uid renvoie le Message-ID recherché
        # par le dernier SEARCH : les tests qui ne s'intéressent pas au
        # filtrage exact n'ont rien à configurer.
        self.message_ids = dict(message_ids or {})
        self.search_status = search_status
        self.fetch_status = fetch_status
        self.copy_status = copy_status
        self.store_status = store_status
        self.move_status = move_status
        self.move_statuses = list(move_statuses) if move_statuses is not None else None
        self.deny_inbox_select = deny_inbox_select
        self.commands = []
        self.selected = None
        self.copied_to = []
        self.moved_to = []
        self.flags_set = []
        self._last_search_value = None

    # -- commandes utilisées par la couche --------------------------------
    def list(self):
        self.commands.append(('LIST',))
        return 'OK', list(self.folders)

    def select(self, mailbox, readonly=False):
        self.commands.append(('SELECT', mailbox, readonly))
        name = mailbox.strip('"').encode()
        if name == b'INBOX' and self.deny_inbox_select:
            return 'NO', [b'inbox temporairement indisponible']
        known = [b'INBOX'] + [f.rsplit(b'"', 2)[-2] for f in self.folders]
        if name not in known:
            return 'NO', [b'no such mailbox']
        self.selected = mailbox
        return 'OK', [b'1']

    def uid(self, command, *args):
        upper = command.upper()
        if not self.selected:
            raise AssertionError(
                'UID %s appelé sans SELECT préalable : un vrai serveur le refuserait' % upper)
        self.commands.append((upper,) + args)

        if upper == 'SEARCH':
            if self.search_status != 'OK':
                return self.search_status, [b'search failed']
            value = args[-1]
            if isinstance(value, str) and value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            self._last_search_value = value
            payload = ' '.join(str(u) for u in self.uids_found).encode()
            return 'OK', [payload]
        if upper == 'FETCH':
            if self.fetch_status != 'OK':
                return self.fetch_status, [b'fetch failed']
            uid = args[0]
            message_id = self.message_ids.get(uid, self._last_search_value)
            header = ('Message-ID: %s\r\n\r\n' % message_id).encode()
            uid_bytes = uid if isinstance(uid, bytes) else str(uid).encode()
            descriptor = b'%s (BODY[HEADER.FIELDS (MESSAGE-ID)] {%d}' % (
                uid_bytes, len(header))
            return 'OK', [(descriptor, header)]
        if upper == 'MOVE':
            if 'MOVE' not in self.capabilities:
                return 'NO', [b'command not supported']
            status = self.move_statuses.pop(0) if self.move_statuses else self.move_status
            if status != 'OK':
                return status, [b'move refused']
            self.moved_to.append(args[1])
            return 'OK', [b'done']
        if upper == 'COPY':
            if self.copy_status != 'OK':
                return self.copy_status, [b'copy failed']
            self.copied_to.append(args[1])
            return 'OK', [b'done']
        if upper == 'STORE':
            if self.store_status != 'OK':
                return self.store_status, [b'store failed']
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

    def test_resolve_decodes_utf7_special_use_name(self):
        # « Ind&AOk-sirables » est l'encodage IMAP-UTF-7 modifié de
        # « Indésirables » : le nom mémorisé doit être décodé, lisible.
        fake = FakeImapServer(folders=[
            b'(\\HasNoChildren \\Junk) "." "Ind&AOk-sirables"',
            b'(\\HasNoChildren) "." "INBOX"',
        ])
        self.assertEqual(self.box._imap_resolve_folder(fake, 'junk'), 'Indésirables')

    def test_force_redetects_ignoring_configured_value(self):
        # Le bouton « Détecter les dossiers » doit pouvoir corriger une
        # détection erronée ou un dossier renommé, pas seulement la remplir
        # une première fois.
        self.box.trash_folder = 'MauvaiseSupposition'
        fake = FakeImapServer()
        result = self.box._imap_resolve_folder(fake, 'trash', force=True)
        self.assertEqual(result, 'INBOX.Trash')
        self.assertEqual(self.box.trash_folder, 'INBOX.Trash')

    def test_force_failure_keeps_previous_value(self):
        # Un nom qui fonctionnait ne doit pas être perdu si la redétection
        # échoue (serveur temporairement muet, par exemple).
        self.box.trash_folder = 'AncienNomValide'
        fake = FakeImapServer(folders=[b'(\\HasNoChildren) "." "INBOX"'])
        with self.assertRaises(UserError):
            self.box._imap_resolve_folder(fake, 'trash', force=True)
        self.assertEqual(self.box.trash_folder, 'AncienNomValide',
                         "un échec de redétection ne doit pas effacer une valeur qui marchait")

    # -- déplacement : cas nominaux ---------------------------------------
    def test_move_uses_move_when_advertised(self):
        fake = FakeImapServer(capabilities=('IMAP4REV1', 'MOVE'))
        result = self.box._imap_move_message(fake, '<abc@example.com>', 'INBOX.Trash')
        self.assertEqual(result, 'moved')
        self.assertEqual(fake.moved_to, ['"INBOX.Trash"'])
        self.assertEqual(fake.copied_to, [], "MOVE disponible : pas de COPY de repli")
        self.assertEqual(fake.selected, 'INBOX',
                         "le déplacement doit sélectionner INBOX, pas hériter d'une sélection antérieure")

    def test_move_falls_back_to_copy_and_uid_expunge(self):
        fake = FakeImapServer(capabilities=('IMAP4REV1', 'UIDPLUS'))
        result = self.box._imap_move_message(fake, '<abc@example.com>', 'INBOX.Trash')
        self.assertEqual(result, 'moved')
        self.assertEqual(fake.copied_to, ['"INBOX.Trash"'])
        self.assertEqual(fake.selected, 'INBOX')
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
        self.assertEqual([c for c in fake.commands if c[0] == 'EXPUNGE'], [],
                         "sans UIDPLUS, aucun EXPUNGE — même ciblé — ne doit être tenté")

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
                    self.assertEqual(command[1], b'7',
                                     "EXPUNGE doit nommer l'UID réellement déplacé, "
                                     "pas une plage : un régresseur qui purgerait tout "
                                     "le dossier doit faire échouer ce test")

    def test_search_uses_header_not_uid(self):
        fake = FakeImapServer(capabilities=('IMAP4REV1', 'MOVE'))
        self.box._imap_move_message(fake, '<abc@example.com>', 'INBOX.Trash')
        search = next(c for c in fake.commands if c[0] == 'SEARCH')
        self.assertIn('HEADER', search)
        self.assertIn('Message-ID', search)

    # -- déplacement : sélection d'INBOX obligatoire -----------------------
    def test_move_selects_inbox_even_after_a_folder_probe(self):
        # Un serveur sans SPECIAL-USE force _imap_resolve_folder à sonder les
        # noms courants par SELECT/EXAMINE, ce qui laisse la connexion
        # sélectionnée sur ce dossier candidat, pas sur INBOX. Le déplacement
        # doit re-sélectionner INBOX lui-même, sinon SEARCH HEADER Message-ID
        # chercherait dans le mauvais dossier et rendrait un 'absent' erroné.
        fake = FakeImapServer(capabilities=('IMAP4REV1', 'MOVE'),
                              folders=[b'(\\HasNoChildren) "." "Trash"',
                                       b'(\\HasNoChildren) "." "INBOX"'])
        self.box._imap_resolve_folder(fake, 'trash')  # laisse la connexion sur "Trash"
        self.assertNotEqual(fake.selected, 'INBOX')
        result = self.box._imap_move_message(fake, '<abc@example.com>', 'INBOX.Trash')
        self.assertEqual(result, 'moved')
        self.assertEqual(fake.selected, 'INBOX')

    def test_move_raises_when_inbox_select_fails(self):
        fake = FakeImapServer(deny_inbox_select=True)
        with self.assertRaises(UserError):
            self.box._imap_move_message(fake, '<abc@example.com>', 'INBOX.Trash')

    # -- déplacement : le SEARCH par sous-chaîne doit être revérifié -------
    def test_move_ignores_substring_match_and_reports_absent(self):
        # SEARCH HEADER peut renvoyer un message dont le Message-ID CONTIENT
        # celui demandé sans lui être égal (RFC 3501 : match par sous-chaîne).
        fake = FakeImapServer(uids_found=(9,), message_ids={b'9': '<sub-abc@example.com>'})
        result = self.box._imap_move_message(fake, '<abc@example.com>', 'INBOX.Trash')
        self.assertEqual(result, 'absent')
        self.assertEqual(fake.moved_to, [])
        self.assertEqual(fake.copied_to, [])

    def test_move_filters_out_substring_false_positive(self):
        fake = FakeImapServer(capabilities=('IMAP4REV1', 'MOVE'), uids_found=(7, 8),
                              message_ids={b'7': '<abc@example.com>',
                                           b'8': '<sub-abc@example.com>'})
        result = self.box._imap_move_message(fake, '<abc@example.com>', 'INBOX.Trash')
        self.assertEqual(result, 'moved')
        self.assertEqual(fake.moved_to, ['"INBOX.Trash"'],
                         "seul le message au Message-ID exact doit être déplacé")

    def test_move_handles_duplicate_message_id_and_downgrades_on_partial_failure(self):
        # Un Message-ID dupliqué (courrier de liste, Bcc-à-soi-même) est
        # ordinaire : les DEUX messages exacts doivent être visés. Si un
        # seul échoue à être déplacé, le résultat global doit le refléter.
        fake = FakeImapServer(capabilities=('IMAP4REV1', 'MOVE'), uids_found=(7, 8),
                              message_ids={b'7': '<abc@example.com>',
                                           b'8': '<abc@example.com>'},
                              move_statuses=['OK', 'NO'])
        result = self.box._imap_move_message(fake, '<abc@example.com>', 'INBOX.Trash')
        self.assertEqual(result, 'copied_not_purged',
                         "un seul déplacement manqué doit dégrader tout le résultat")
        self.assertEqual(fake.moved_to, ['"INBOX.Trash"'])
        self.assertEqual(fake.copied_to, ['"INBOX.Trash"'])

    # -- déplacement : la fiabilité de chaque commande est vérifiée --------
    def test_search_failure_raises_user_error(self):
        fake = FakeImapServer(search_status='NO')
        with self.assertRaises(UserError):
            self.box._imap_move_message(fake, '<abc@example.com>', 'INBOX.Trash')

    def test_copy_failure_raises_user_error(self):
        fake = FakeImapServer(capabilities=('IMAP4REV1',), copy_status='NO')
        with self.assertRaises(UserError):
            self.box._imap_move_message(fake, '<abc@example.com>', 'INBOX.Trash')

    def test_move_refused_by_server_falls_back_to_copy(self):
        # MOVE annoncé dans les capabilities mais refusé pour cette commande
        # précise (quota, dossier en lecture seule...) : repli sur COPY.
        fake = FakeImapServer(capabilities=('IMAP4REV1', 'MOVE'), move_status='NO')
        result = self.box._imap_move_message(fake, '<abc@example.com>', 'INBOX.Trash')
        self.assertEqual(result, 'copied_not_purged')
        self.assertEqual(fake.moved_to, [])
        self.assertEqual(fake.copied_to, ['"INBOX.Trash"'])

    def test_store_failure_prevents_expunge_and_downgrades(self):
        # Si le \\Deleted ne s'est pas posé (dossier en lecture seule, quota,
        # droits refusés), un EXPUNGE — même ciblé — ne purgerait rien pour
        # ce message et ne doit pas être tenté ; le résultat doit rendre
        # compte de l'échec plutôt que de mentir en rendant 'moved'.
        fake = FakeImapServer(capabilities=('IMAP4REV1', 'UIDPLUS'), store_status='NO')
        result = self.box._imap_move_message(fake, '<abc@example.com>', 'INBOX.Trash')
        self.assertEqual(result, 'copied_not_purged')
        self.assertEqual([c for c in fake.commands if c[0] == 'EXPUNGE'], [],
                         "sans le flag \\Deleted posé, EXPUNGE ne doit pas être tenté")

    # -- capacités absentes -------------------------------------------------
    def test_missing_capabilities_attribute_defaults_to_empty(self):
        # `capabilities` est un attribut d'INSTANCE posé après connexion par
        # imaplib, jamais un attribut de classe : sur une connexion qui ne
        # l'a pas encore, la couche ne doit planter ni tenter MOVE/EXPUNGE.
        fake = FakeImapServer(capabilities=('IMAP4REV1', 'UIDPLUS'))
        del fake.capabilities
        result = self.box._imap_move_message(fake, '<abc@example.com>', 'INBOX.Trash')
        self.assertEqual(result, 'copied_not_purged')
        self.assertEqual(fake.moved_to, [])
        self.assertEqual([c for c in fake.commands if c[0] == 'EXPUNGE'], [])

    # -- noms de dossiers accentués -----------------------------------------
    def test_move_encodes_accented_folder_name(self):
        fake = FakeImapServer(capabilities=('IMAP4REV1', 'MOVE'))
        result = self.box._imap_move_message(fake, '<abc@example.com>', 'Indésirables')
        self.assertEqual(result, 'moved')
        self.assertEqual(fake.moved_to, ['"Ind&AOk-sirables"'],
                         "un nom de dossier accentué doit partir en UTF-7 modifié sur le fil")

    # -- UTF-7 modifié : les délimiteurs ASCII ne doivent jamais être touchés
    def test_utf7_encode_preserves_ascii_delimiters(self):
        # Une substitution globale de + et / corromprait ces noms : Gmail
        # nomme littéralement ses dossiers spéciaux "[Gmail]/Trash" etc.
        self.assertEqual(self.box._imap_utf7_encode('[Gmail]/Trash'), '[Gmail]/Trash')
        self.assertEqual(self.box._imap_utf7_encode('[Gmail]/Corbeille'), '[Gmail]/Corbeille')
        self.assertEqual(self.box._imap_utf7_encode('C++'), 'C++')

    def test_utf7_encode_escapes_literal_ampersand(self):
        # Un & littéral doit sortir en &- ; laissé nu, le serveur lirait le
        # reste du nom comme une séquence UTF-7 non terminée.
        self.assertEqual(self.box._imap_utf7_encode('R&D'), 'R&-D')

    def test_utf7_encode_accented_name_matches_wire_form(self):
        self.assertEqual(self.box._imap_utf7_encode('Indésirables'), 'Ind&AOk-sirables')

    def test_utf7_round_trip_ascii_and_accented_names(self):
        for name in ('[Gmail]/Trash', 'R&D', 'C++', 'Indésirables',
                     'Éléments supprimés', 'INBOX.Trash'):
            encoded = self.box._imap_utf7_encode(name)
            self.assertEqual(self.box._imap_utf7_decode(encoded), name,
                             "aller-retour cassé pour %r" % name)

    def test_utf7_decode_never_raises_on_malformed_input(self):
        # Une séquence & jamais refermée par un - ne doit jamais faire
        # planter le bouton « Détecter les dossiers » sur une trace Python.
        self.assertEqual(self.box._imap_utf7_decode('R&AOk'), 'R&AOk')
        self.assertEqual(self.box._imap_utf7_decode('foo&'), 'foo&')

    def test_parse_list_name_decodes_raw_utf8_without_raising(self):
        # Un serveur RFC 6855 peut envoyer un nom LIST déjà en UTF-8 brut,
        # sans passer par l'UTF-7 modifié.
        line = b'(\\HasNoChildren) "." "Ind\xc3\xa9sirables"'
        self.assertEqual(self.box._imap_parse_list_name(line), 'Indésirables')

    # -- filtrage exact du Message-ID : au-delà du simple préfixe -----------
    def test_move_ignores_suffix_extended_match_and_reports_absent(self):
        # Le Message-ID fetché COMMENCE par celui recherché sans lui être
        # égal : un `startswith(target)` laisserait passer ce faux positif
        # là où seule l'égalité stricte est correcte.
        fake = FakeImapServer(uids_found=(9,),
                              message_ids={b'9': '<abc@example.com>-old'})
        result = self.box._imap_move_message(fake, '<abc@example.com>', 'INBOX.Trash')
        self.assertEqual(result, 'absent')
        self.assertEqual(fake.moved_to, [])
        self.assertEqual(fake.copied_to, [])

    # -- un FETCH en échec ne doit jamais se travestir en « absent » --------
    def test_fetch_failure_raises_user_error_instead_of_reporting_absent(self):
        # Si le FETCH échoue pour l'unique candidat, on ne sait pas s'il
        # s'agit du message cherché : rendre 'absent' mentirait (c'est un
        # succès contractuel) pour un message peut-être toujours présent.
        fake = FakeImapServer(uids_found=(7,), fetch_status='NO')
        with self.assertRaises(UserError):
            self.box._imap_move_message(fake, '<abc@example.com>', 'INBOX.Trash')
