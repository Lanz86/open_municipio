Istruzioni per installare un'istanza di open_municipio sul proprio PC.

Prerequisiti
============

L'ambiente di sviluppo deve verificare i [requisiti Django](http://docs.djangoproject.com/en/dev/faq/install/).

Per comodità, viene usato il tool [virtualenv](http://www.arthurkoziel.com/2008/10/22/working-virtualenv/), che permette
l'isolamento dell'ambiente di sviluppo.

Per ulteriore comodità, vengono usati gli script [virtualenvwrapper](http://www.doughellmann.com/docs/virtualenvwrapper/), che permettono di accedere velocemente ai comandi di virtualenv per il setup di environment e la loro gestione.

Una volta installato un gestore di pacchetti python, si può procedere semplicemente con l'installazione di entrambi i pacchetti:

    pip install virtualenv
    pip install virtualenvwrapper



Definizione ambiente di progetto, per Django con `virtualenv`
=============================================================

Creare un virtualenv, usando `virtualenv_wrapper`

    mkvirtualenv open_municipio
    mkdir -p /home/open_municipio

Poi, in `~/.virtualenvs/open_municipio/bin/`, modificare `postactivate` e `postdeactivate`, in modo che dopo l'attivazione dell'environment, la working dir diventi `/home/open_municipio`.

Si tratta di script che vengono lanciati dopo l'attivazione del virtualenv (`workon open_municipio`) o dopo 
la disattivazione. Vengono settate alcune variabili di environment per poter lavorare sul progetto comodamente.

**postactivate**

    #!/bin/bash
    # This hook is run after this virtualenv is activated.
    cd /home/open_municipio
    export OLD_PYTHONPATH=$PYTHONPATH
    export PYTHONPATH=/home/open_municipio:$PYTHONPATH
    export DJANGO_SETTINGS_MODULE=opm_site.settings

**postdeactivate**

    #!/bin/bash
    # This hook is run after this virtualenv is deactivated.
    cd ~/
    export PYTHONPATH=$OLD_PYTHONPATH
    unset OLD_PYTHONPATH
    unset DJANGO_SETTINGS_MODULE

Installare, nel virtualenv, i pacchetti software che saranno utilizzati.

    pip install django - il web framework
    pip install django-extensions - estensioni al framework utili per stare più comodi
    pip install south - applicazione django per gestire le migrazioni del DB
    pip install MySQL-python - driver mysql (opzionale)
    pip install django-piston - per costruire le API REST dal modello (opzionale)


Dopo la generazione dell'ambiente virtualenv, per accedervi e lavorare:

    workon open_municipio
    
mentre, per terminare la sessione di lavoro:

    deactivate
    



Struttura delle directory
=========================
    open_municipio
    |- om
    |  |- models.py
    |  |- views.py
    |  |- admin.py
    |- opm_site
    |  |- templates
    |  |- settings.py


Il progetto web è in `opm_site`, e contiene il frontend. Si basa sull'applicazione `om`, che vive di vita propria,
in modo da potere essere usata da progetti diversi (diversi templates, canali, ...).
L'applicazione costituisce il backend, permette la modifica e la verifica dei dati ed espone i dati attraverso una API piston.

Il sito usa l'applicazione attraverso la API o in altri modi da stabilire più avanti.


Creazione e gestione DB e migrazioni con south
==============================================
Il DB e le sue tabelle vanno create con 

    django-admin.py syncdb

Nel caso di un db Mysql o Postgres, bisogna prima creare il DB, 
nel caso si utilizzi sqlite3, si può lasciar fare a Django.

Per modificare lo schema del DB in modo agile, evitando la rimozione dei dati già inseriti
(alter invece di drop + create) si può usare `south` (http://south.aeracode.org/).

Per creare la prima migrazione e allineare il modello al db:

    django-admin.py schemamigration om --initial
    django-admin.py migrate om



In seguito a una modifica del modello:

    django-admin.py schemamigration om --auto
    django-admin.py migrate om


Directory uploads
=================
La directory che tiene gli uploads deve essere definita nei settings. Io ho scelto `/home/open_municipio/uploads`
perché è fuori da qualsiasi directory esposta sul web. A questa cartella devono essere dati i permessi di scrittura per
l'utente web.

La directory contiene una subdirectory allegati, che contiene, raggruppati per giorno (formato yyyymmdd) gli allegati
caricati dall'interfaccia di backend (o da script di importazione).


