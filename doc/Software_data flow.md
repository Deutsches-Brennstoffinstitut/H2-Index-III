## GUI initialization
### 0) MainGUI.mlapp - startupFcn
```
[app.Framework] = initialize_GUI_Framework();   
[app.BaseLib]   = initialize_database();   
DisableCheckboxes(app) % Keine freie Auswahl der Module   
app.UpdateMainWindow()   
```

### 0.1) initialize_GUI_Framework
1) set up Value chain "A" as default
```
Framework.ChoiceOfBWK       = 'A) RE Based Production H2';   
Framework.ModeOfOperation   = 'Single Value Chain';
```

2) set up default parameter sweep options    
``` 
Framework.ParameterSweep.Options  = false; 
[ParameterOptions] = initialize_BWK_SweepParameter('A');  
```

### 0.2) [BaseLib] = initialize_database()
1) read Baselib.mat
2) read normalized Curves for Wind + PV

### 0.3 UpdateMainWindow()
Value chain specific Initialization: (BWK = "Basis Wertschoepfungs Kette")

````
app                                             = initialize_BWK_boxes(app, BWK_Letter);
[app.Framework.KPP, app.Framework.KPI]          = initialize_BWK_KPI(app.BaseLib, BWK_Letter);
[app.Framework.KEP]                             = initialize_BWK_KEP(app.BaseLib, BWK_Letter, app.Framework.KPI);  
app.Framework.ParameterSweep.ParameterOptions   = initialize_BWK_SweepParameter(BWK_Letter);
[app.Profile]                                   = initialize_BWK_Profiles(BWK_Letter, app.BaseLib, app.Framework);
````
#### 0.3.1 initialize_BWK_boxes
set up MAIN GUI interactivity
#### 0.3.2 initialize_BWK_KPI
set up for each component:
- initial scaling/ nominal power
- initial capacities
- initial 
- hours of full load
- maintennacane dates
#### 0.3.3 initialize_BWK_KEP
set up for each component:
- Cost Parameters, CAPEX OPEX fix etc....
TODO specifz this list

#### 0.3.4 initialize_BWK_SweepParameter
set up sweep parameter options for each
- Value chain
- Component in this value chain

#### 0.3.5 initialize_BWK_Profiles
set up for each Value chain
- profilese for  
  - demand
  - production
