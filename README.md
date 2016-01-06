# PyomoApp

# GAMSApp

plugin_name: PyomoExporter
--------------------------
The plug-in provides an easy to use tool for exporting data from
HydraPlatform to custom Pyomo models. The basic idea is that this plug-in
exports a network and associated data from HydraPlatform to a text file which
can be imported into an existing Pyomo model.

**Mandatory Args:**


====================== ====== ========== ======================================
Option                 Short  Parameter  Description
====================== ====== ========== ======================================
--network              -t     NETWORK    ID of the network where results will
                                         be imported to. Ideally this coincides
                                         with the network exported to Pyomo.
--scenario            -s     SCENARIO    ID of the underlying scenario used for
                                          simulation
--template-id         -tp    TEMPLATE    ID of the template used for exporting
                                         resources. Attributes that don't
                                         belong to this template are ignored.
--output              -o    OUTPUT       Filename of the output file.
====================== ====== ========== ======================================

**Server-based arguments:**

====================== ====== ========== =========================================
Option                 Short  Parameter  Description
====================== ====== ========== =========================================
--server_url           -u     SERVER_URL   Url of the server the plugin will 
                                           connect to.
                                           Defaults to localhost.
--session_id           -c     SESSION_ID   Session ID used by the calling software 
                                           If left empty, the plugin will attempt 
                                           to log in itself.
====================== ====== ========== =========================================

**Switches:**

====================== ====== =========================================
Option                 Short  Description
====================== ====== =========================================
--export_by_type       -et    Set export data based on types or 
                              based on attributes only, default is 
                              export data by attributes unless this 
                              option is set.
====================== ====== =========================================

Specifying the time axis
~~~~~~~~~~~~~~~~~~~~~~~~

One of the following two options for specifying the time domain of the model is
mandatory:

**Option 1:**

====================== ====== ========== ======================================
Option                 Short  Parameter  Description
====================== ======= ========== ======================================
--start-date            -st   START_DATE  Start date of the time period used for
                                          simulation.
--end-date              -en   END_DATE    End date of the time period used for
                                          simulation.
--time-step             -dt   TIME_STEP   Time step used for simulation. The
                                          time step needs to be specified as a
                                          valid time length as supported by
                                          Hydra's unit conversion function (e.g.
                                          1 s, 3 min, 2 h, 4 day, 1 mon, 1 yr)
====================== ======= ========== ======================================

**Option 2:**

====================== ====== ========== ======================================
Option                 Short  Parameter  Description
====================== ======= ========== ======================================
--time-axis             -tx    TIME_AXIS  Time axis for the modelling period (a
                                          list of comma separated time stamps).
====================== ======= ========== ======================================
===============================================================================

plugin_name: PyomoAutoRun
--------------------------

The plug-in provides an easy way to:

            - Export a network from Hydra to a pyomo input text file.
            - Rum pyomo model.
            - Import a results into Hydra.

**Mandatory Args:**

====================== ====== ========== ======================================
Option                 Short  Parameter  Description
====================== ====== ========== ======================================
--network              -t     NETWORK    ID of the network where results will
                                         be imported to. Ideally this coincides
                                         with the network exported to Pyomo.
--scenario             -s     SCENARIO   ID of the underlying scenario used for
                                         simulation
--template-id          -tp    TEMPLATE   ID of the template used for exporting
                                         resources. Attributes that don't
                                         belong to this template are ignored.
--output               -o     OUTPUT     Filename of the output file.
--model               -m      MODEL      Pyomo model file (*.py), needs to have
                                         a method called run_model which 
                                         takes the datafile as an argument and 
                                         return 2 lists containing results and 
                                         model instances. Example is provided 
                                         with the plugin
====================== ====== ========== ======================================

**Server-based arguments**

====================== ====== ========== =======================================
Option                 Short  Parameter  Description
====================== ====== ========== =======================================
--server_url           -u     SERVER_URL Url of the server the plugin will 
                                         connect to.
                                         Defaults to localhost.
--session_id           -c     SESSION_ID Session ID used by the calling software
                                         If left empty, the plugin will attempt 
                                         to log in itself.
====================== ====== ========== =======================================

**Switches:**

====================== ====== =========================================
Option                 Short  Description
====================== ====== =========================================
--export_by_type       -et    Set export data based on types or 
                              based on attributes only, default is 
                              export data by attributes unless this
                              option is set.
====================== ====== =========================================

Specifying the time axis
~~~~~~~~~~~~~~~~~~~~~~~~

One of the following two options for specifying the time domain of the model is
mandatory:

**Option 1:**

====================== ====== ========== ======================================
Option                 Short  Parameter  Description
====================== ====== ========== ======================================
--start-date            -st   START_DATE  Start date of the time period used for
                                          simulation.
--end-date              -en   END_DATE    End date of the time period used for
                                          simulation.
--time-step             -dt   TIME_STEP   Time step used for simulation. The
                                          time step needs to be specified as a
                                          valid time length as supported by
                                          Hydra's unit conversion function (e.g.
                                          1 s, 3 min, 2 h, 4 day, 1 mon, 1 yr)
====================== ====== ========== ======================================

**Option 2:**

====================== ====== ========== ======================================
Option                 Short  Parameter  Description
====================== ====== ========== ======================================
--time-axis             -tx    TIME_AXIS  Time axis for the modelling period (a
                                          list of comma separated time stamps).
====================== ====== ========== ======================================
===============================================================================

plugin_name: PyomoRunImport
---------------------------

The plug-in provides an easy way to:

            - Rum pyomo model.
            - Import a results into Hydra.
			
mandatory_args
==============

====================== ====== ========== ======================================
Option                 Short  Parameter  Description
====================== ====== ========== ======================================
--network              -t     NETWORK    ID of the network where results will
                                         be imported to. Ideally this coincides
                                         with the network exported to Pyomo.
--scenario            -s     SCENARIO    ID of the underlying scenario used for
                                          simulation
--template-id         -tp    TEMPLATE    ID of the template used for exporting
                                         resources. Attributes that don't
                                         belong to this template are ignored.
--output              -o    OUTPUT       Filename of the output file.

-- model              -m    Pyomo model  Pyomo model file (*.py), needs to implement a method called
                            file         run_model which takes the datafile as an argument and returns
                                         2 lists containing results and model instances. Example is
                                         distributed with the plugin


Server-based arguments
======================

====================== ====== ========== =========================================
Option                 Short  Parameter  Description
====================== ====== ========== =========================================
``--server_url``       ``-u`` SERVER_URL   Url of the server the plugin will 
                                           connect to.
                                           Defaults to localhost.
``--session_id``       ``-c`` SESSION_ID   Session ID used by the calling software
                                           If left empty, the plugin will attempt 
                                           to log in itself.