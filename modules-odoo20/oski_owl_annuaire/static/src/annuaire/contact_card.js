import { Component, t, useProps } from "@odoo/owl";

/** Carte d'une société : n'affiche que ce que le parent lui passe. */
export class ContactCard extends Component {
    static template = "oski_owl_annuaire.ContactCard";

    props = useProps({
        partner: t.object({ id: t.number(), name: t.string() }),
        isFavorite: t.boolean().optional(false),
        onToggleFavorite: t.function(),
    });

    toggle() {
        this.props.onToggleFavorite(this.props.partner.id);
    }
}
