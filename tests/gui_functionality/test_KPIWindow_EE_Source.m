
classdef test_KPIWindow_EE_Source < matlab.uitest.TestCase% subclass of matlab.uitest.TestCase
    properties
        MainApp                                 % will hold the GUI Framework
        ValueChains                             % entries to the Value chain drop down menue
        Window_Name = 'KPIWindow_EE_Sources';   % the KPI Window for which these tests are relevant
        list_of_valuechains = [1, 3, 4];              % list ov Value chains ID#s where this window is relevant
    end
    
    methods (TestMethodSetup)
        function launchApp(testCase)
            addpath(genpath('..\..\base_python'));
            addpath(genpath('..\..\base_matlab'));
            addpath(genpath('..\..\data'));
            testCase.MainApp = MainGUI(); % Get handle to Main App
            testCase.addTeardown(@delete,testCase.MainApp);
            testCase.ValueChains = testCase.MainApp.DropDown_ChooseWSK.Items; % all entries in the dropdown menue
        end
    end
      
    
    methods (Test)
        function open_and_close(testCase)

            %% must also work for BWK A without clicking the dropdown first:
            testCase.assertEqual(testCase.MainApp.DirectSupplyCheckBox.Value,true)
            % open and Close the Window
            open_close_KPI_Window(testCase,testCase.Window_Name, testCase.MainApp.Button_PowerCreation);
            
            % set up Main GUI
            testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
            % test opening and closing for each relevant Value chain: 
            % After clicking the dropdown
            for Index = testCase.list_of_valuechains
                Drop_down_entry = testCase.ValueChains{Index}; % indes is  number of value chain)% indes is only number of entry (which then gives the number of value chain)
                % disp(Drop_down_entry)
                testCase.choose(testCase.MainApp.DropDown_ChooseWSK,Drop_down_entry);
                testCase.assertEqual(testCase.MainApp.DirectSupplyCheckBox.Value,true)
                % open and Close the Window
                open_close_KPI_Window(testCase,testCase.Window_Name, testCase.MainApp.Button_PowerCreation);
            end
            testCase.MainApp.TearDown;
        end
        
        function Zubau_Index(testCase)
            % set up Main GUI
            testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
            % test opening and closing for each relevant Value chain:
            for Index = testCase.list_of_valuechains
                Drop_down_entry = testCase.ValueChains{Index}; % indes is  number of value chain)
                disp(Drop_down_entry)
                testCase.choose(testCase.MainApp.DropDown_ChooseWSK, Drop_down_entry);
                testCase.assertEqual(testCase.MainApp.DirectSupplyCheckBox.Value,true)
                % open the KPI Window
                testCase.press(testCase.MainApp.Button_PowerCreation);

                %% set PV and wind new installment to none Zero:
                % https://www.mathworks.com/help/matlab/matlab_prog/overview-of-app-testing-framework.html
                if ~testCase.MainApp.Framework.KPI.EnergySupply.Wind_ZubauIndikator % if NOT True
                    testCase.choose(testCase.MainApp.KPIWindow.UITableStromAnlagen, [1,3], true) % set True
                end
                if ~testCase.MainApp.Framework.KPI.EnergySupply.PV_ZubauIndikator      % if NOT True   
                    testCase.choose(testCase.MainApp.KPIWindow.UITableStromAnlagen, [2,3], true) % set True
                end
                % this should have triggered an update of these:
                testCase.assertEqual(testCase.MainApp.Framework.KPI.EnergySupply.Wind_ZubauIndikator, true)
                testCase.assertEqual(testCase.MainApp.Framework.KPI.EnergySupply.PV_ZubauIndikator, true)
                %Berechnung starten
                testCase.press(testCase.MainApp.BerechnungStartenButton);
                %Ergebnisse anzeigen:
                testCase.press(testCase.MainApp.ResultsButton);
                testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
                testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_SingleRun')
                % --> results should show some CAPEX for RE
                verifyGreaterThan(testCase, testCase.MainApp.ResultsWindow.CAPEXEditField.Value, 0)
                
                %% set PV and wind new installment to Zero:
                %app.ParentFramework.Framework.KPI.EnergySupply.Wind_ZubauIndikator
                testCase.choose(testCase.MainApp.KPIWindow.UITableStromAnlagen, [1,3], false)
                %app.ParentFramework.Framework.KPI.EnergySupply.PV_ZubauIndikator         
                testCase.choose(testCase.MainApp.KPIWindow.UITableStromAnlagen, [2,3], false)
                
                % this should have triggered an update of these:
                testCase.assertEqual(testCase.MainApp.Framework.KPI.EnergySupply.Wind_ZubauIndikator, false)
                testCase.assertEqual(testCase.MainApp.Framework.KPI.EnergySupply.PV_ZubauIndikator, false)

                %Berechnung starten
                testCase.press(testCase.MainApp.BerechnungStartenButton);
                %Ergebnisse anzeigen:
                testCase.press(testCase.MainApp.ResultsButton);
                testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
                testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_SingleRun')
                % --> results should show no CAPEX for RE
                testCase.assertEqual(testCase.MainApp.ResultsWindow.CAPEXEditField.Value, 0)

            end
            testCase.MainApp.TearDown;
        end

        function zero_nominal_power(testCase)
            % set up Main GUI
            testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
            % test opening and closing for each relevant Value chain:
            for Index = testCase.list_of_valuechains
                Drop_down_entry = testCase.ValueChains{Index}; % indes is only number of entry (which then gives the number of value chain)
                testCase.choose(testCase.MainApp.DropDown_ChooseWSK, Drop_down_entry);
                testCase.assertEqual(testCase.MainApp.DirectSupplyCheckBox.Value,true)
                % open and Close the Window
                testCase.press(testCase.MainApp.Button_PowerCreation);
                %% set PV + Wind Power to Zero
                %app.ParentFramework.Framework.KPI.EnergySupply.Wind_NominalPower     
                testCase.type(testCase.MainApp.KPIWindow.UITableStromAnlagen, [1,2], "0") 
                %app.ParentFramework.Framework.KPI.EnergySupply.PV_NominalPower 
                testCase.type(testCase.MainApp.KPIWindow.UITableStromAnlagen, [2,2], "0") 
                
                %Berechnung starten
                testCase.press(testCase.MainApp.BerechnungStartenButton);
                %Ergebnisse anzeigen:
                testCase.press(testCase.MainApp.ResultsButton);
                testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
                testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_SingleRun')
                
                % --> results should show no CAPEX for RE
                testCase.assertEqual(testCase.MainApp.ResultsWindow.CAPEXEditField.Value, 0)

                % --> results should show no produced Power
                testCase.assertEqual(testCase.MainApp.ResultsWindow.CAPEXEditField.Value, 0)

                % --> results should show no produced Hydrogen
                testCase.assertEqual(testCase.MainApp.ResultsWindow.CAPEXEditField.Value, 0)

                % --> no Cost for Production of Power
                testCase.assertEqual(testCase.MainApp.ResultsWindow.CAPEXEditField.Value, 0)

            end
            testCase.MainApp.TearDown;
        end 

        function edit_profiles(testCase)
            % set up Main GUI
            testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
            % test opening and closing for each relevant Value chain:
            for Index = testCase.list_of_valuechains
                Drop_down_entry = testCase.ValueChains{Index};
                disp(Drop_down_entry)
                testCase.choose(testCase.MainApp.DropDown_ChooseWSK, Drop_down_entry);
                testCase.assertEqual(testCase.MainApp.DirectSupplyCheckBox.Value,true)
                % open and Close the Window
                testCase.press(testCase.MainApp.Button_PowerCreation);

                %% set PV  to 1 oder so
                disp('testing pv')
                %app.ParentFramework.Framework.KPI.EnergySupply.PV_NominalPower  
                testCase.type(testCase.MainApp.KPIWindow.UITableStromAnlagen, [1,2], "0") 
                
                %% edit the other, nonzero source
                testCase.press(testCase.MainApp.KPIWindow.StromquellenbearbeitenButton); 
                %testCase.choose(testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.ArtderErzeugungNeuesProfilDropDown, "Wind")
                testCase.choose(testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.ArtderErzeugungNeuesProfilDropDown, "PV")

                testCase.press(testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.get_Map_GUI_profile)
                testCase.type(testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.Map_GUI_Window.FindLocationEditField, "Leipzig")

                % assert that location has been found
                % tmp save pv profile
                tmp_PV_curve = testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.Map_GUI_Window.PV_curve; 
                testCase.press(testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.Map_GUI_Window.UsePVProfileButton)


                %Berechnung starten
                testCase.press(testCase.MainApp.BerechnungStartenButton);
                %Ergebnisse anzeigen:
                testCase.press(testCase.MainApp.ResultsButton);
                testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);

                % assert that production sum profile is the tmp saved RE
                % profile from earlier:
                testCase.assertEqual(testCase.MainApp.Profile.EnergySupply.Produced, tmp_PV_curve);

                %% same for wind:
                disp('testing pv')
                %app.ParentFramework.Framework.KPI.EnergySupply.PV_NominalPower  
                testCase.type(testCase.MainApp.KPIWindow.UITableStromAnlagen, [2,2], "0") 
                
                %% edit the other, nonzero source
                testCase.press(testCase.MainApp.KPIWindow.StromquellenbearbeitenButton); 
                testCase.choose(testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.ArtderErzeugungNeuesProfilDropDown, "Wind")
                
                testCase.press(testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.get_Map_GUI_profile)
                testCase.type(testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.Map_GUI_Window.FindLocationEditField, "Leipzig")

                % assert that location has been found
                % tmp save windprofile 
                tmp_WIND_curve = testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.Map_GUI_Window.WKA_curve; 
                testCase.press(testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.Map_GUI_Window.UseWindProfileButton)

                %Berechnung starten
                testCase.press(testCase.MainApp.BerechnungStartenButton);
                %Ergebnisse anzeigen:
                testCase.press(testCase.MainApp.ResultsButton);
                testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);

                % assert that production sum profile is the tmp saved RE
                % profile from earlier:
                testCase.assertEqual(testCase.MainApp.Profile.EnergySupply.Produced, tmp_WIND_curve);

            end
        end


        function read_profiles_standard(testCase)
            FileName = "..\\test_profiles\\01_standard.xlsx";
            % set up Main GUI
            testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
            % test opening and closing for each relevant Value chain:
            for Index = testCase.list_of_valuechains
                Drop_down_entry = testCase.ValueChains{Index};
                disp(Drop_down_entry)
                testCase.choose(testCase.MainApp.DropDown_ChooseWSK, Drop_down_entry);
                testCase.assertEqual(testCase.MainApp.DirectSupplyCheckBox.Value,true)
                % open and Close the Window
                testCase.press(testCase.MainApp.Button_PowerCreation);

                %% set PV  to 1 oder so
                disp('testing pv')
                %app.ParentFramework.Framework.KPI.EnergySupply.PV_NominalPower  
                testCase.type(testCase.MainApp.KPIWindow.UITableStromAnlagen, [1,2], "0") 
                
                %% edit the other, nonzero source
                testCase.press(testCase.MainApp.KPIWindow.StromquellenbearbeitenButton); 
                %testCase.choose(testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.ArtderErzeugungNeuesProfilDropDown, "Wind")
                testCase.choose(testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.ArtderErzeugungNeuesProfilDropDown, "PV")

                [testCase, tmp_curve]  = test_NeuesProfileinlesenButtonPushed(testCase, FileName);
                
                %Berechnung starten
                testCase.press(testCase.MainApp.BerechnungStartenButton);
                %Ergebnisse anzeigen:
                testCase.press(testCase.MainApp.ResultsButton);
                testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);

                % assert that production sum profile is the tmp saved RE
                % profile from earlier:
                testCase.assertEqual(testCase.MainApp.Profile.EnergySupply.Produced, tmp_curve);

                %% same for wind:
                disp('testing pv')
                %app.ParentFramework.Framework.KPI.EnergySupply.PV_NominalPower  
                testCase.type(testCase.MainApp.KPIWindow.UITableStromAnlagen, [2,2], "0") 
                
                %% edit the other, nonzero source
                testCase.press(testCase.MainApp.KPIWindow.StromquellenbearbeitenButton); 
                testCase.choose(testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.ArtderErzeugungNeuesProfilDropDown, "Wind")
                
                testCase.press(testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.get_Map_GUI_profile)
                testCase.type(testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.Map_GUI_Window.FindLocationEditField, "Leipzig")

                % assert that location has been found
                % tmp save windprofile 
                [testCase, tmp_curve]  = test_NeuesProfileinlesenButtonPushed(testCase, FileName);

                %Berechnung starten
                testCase.press(testCase.MainApp.BerechnungStartenButton);
                %Ergebnisse anzeigen:
                testCase.press(testCase.MainApp.ResultsButton);
                testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);

                % assert that production sum profile is the tmp saved RE
                % profile from earlier:
                testCase.assertEqual(testCase.MainApp.Profile.EnergySupply.Produced, tmp_curve);

            end
        testCase.MainApp.TearDown;       
        end % of single test
    end % of testing methods
end % of classdef


