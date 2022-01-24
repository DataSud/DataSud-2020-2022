# IDGO CADASTRE ORDER

## Configuration

#### Dans le fichier `settings.py` de l'application :

##### Ajouter l'application :

```python
INSTALLED_APPS = [
    # (...)
    'idgo_admin',
    'idgo_cadastre_order',
    # (...)
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # (...)
                'idgo_cadastre_order.context_processors.global_vars',
                # (...)
            ],
        },
    },
]


# Mandatory:

IDGO_CADASTRE_ORDER_CONTACT_EMAIL = ''
IDGO_CADASTRE_ORDER_COMMITMENT_HREF = ''

# Optional:

IDGO_CADASTRE_ORDER_CC_EMAIL = []
IDGO_CADASTRE_ORDER_DPO_HREF = 'https://www.cnil.fr/fr/designation-dpo'
IDGO_CADASTRE_ORDER_PROCESSING_TIME = '15 jours'
IDGO_CADASTRE_ORDER_DOCUMENTATION = 'https://...'
IDGO_CADASTRE_ORDER_REDUCED_TO_PARTNER = True
```


#### Dans le fichier `urls.py` de l'application :

```python
urlpatterns = [
    # (...)
    url(r'^cadastre/order/', include('idgo_cadastre_order.urls', namespace='idgo_cadastre_order')),
    # (...)
]
```
