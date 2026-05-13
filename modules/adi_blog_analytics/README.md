# ADI - Blog Analytics

Application Odoo 19 — tableau de bord backend pour piloter la croissance éditoriale d'un blog Odoo.

## KPIs V1

- **Inscrits newsletter** (mailing.contact) par jour + par pays
- **Vues d'articles** (website.track filtré /blog/%) par jour
- **Top articles** (blog.post ordonné par visits DESC)

## Filtres temps

Aujourd'hui · Ce mois · Mois dernier · 7 derniers jours · 30 derniers jours · custom range.

## Dépendances

- `website_blog`, `mass_mailing`, `website` (modules natifs Odoo)
- Recommandé : `adi_blog_geoip` (résout `country_id` automatiquement à l'inscription)

## Installation

```bash
./odoo-bin -i adi_blog_analytics -d <database> --stop-after-init
```

Puis attribuer le groupe "Blog Analytics Viewer" aux utilisateurs concernés dans Settings → Utilisateurs.

## Auteur

ADICOPS — https://odooskills.com — LGPL-3
