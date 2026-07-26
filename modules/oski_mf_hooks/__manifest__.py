{
    'name': 'OdooSkills — Ordre des hooks',
    'version': '19.0.1.0.0',
    'author': 'OdooSkills',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': ['data/demo_record.xml'],
    'pre_init_hook': '_pre_init',
    'post_init_hook': '_post_init',
    'uninstall_hook': '_uninstall',
    'post_load': '_post_load',
    'installable': True,
}
