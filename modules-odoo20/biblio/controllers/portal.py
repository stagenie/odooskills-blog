from odoo.exceptions import AccessError, MissingError
from odoo.http import request, route

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class LibraryPortal(CustomerPortal):

    def _prepare_portal_counter_values(self, counter):
        if counter == 'library_loan_count':
            return 'library.loan', [], 'read'
        return super()._prepare_portal_counter_values(counter)

    @route()
    def counters(self, counters, **kw):
        res = super().counters(counters, **kw)
        if 'library_loan_count' in res:
            res['library_loan_count'] = request.env['library.loan'].search_count([])
        return res

    @route(['/my/loans', '/my/loans/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_loans(self, page=1, **kw):
        Loan = request.env['library.loan']
        loan_count = Loan.search_count([])
        pager = portal_pager(
            url='/my/loans',
            total=loan_count,
            page=page,
            step=self._items_per_page,
        )
        loans = Loan.search([], limit=self._items_per_page, offset=pager['offset'])
        request.session['my_loans_history'] = loans.ids[:100]

        values = self._prepare_portal_layout_values()
        values.update({
            'loans': loans.sudo(),
            'page_name': 'library_loan',
            'default_url': '/my/loans',
            'pager': pager,
        })
        return request.render('biblio.portal_my_loans', values)

    @route('/my/loans/<int:loan_id>', type='http', auth='public', website=True)
    def portal_my_loan(self, loan_id, access_token=None, **kw):
        try:
            loan_sudo = self._document_check_access('library.loan', loan_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._get_page_view_values(
            loan_sudo, access_token, {'page_name': 'library_loan'},
            'my_loans_history', False, **kw,
        )
        values['loan'] = loan_sudo
        return request.render('biblio.portal_my_loan', values)
