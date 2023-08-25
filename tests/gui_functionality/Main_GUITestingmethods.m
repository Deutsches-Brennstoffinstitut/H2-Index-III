% https://www.mathworks.com/help/matlab/matlab_prog/overview-of-app-testing-framework.html

classdef Main_GUITestingmethods < matlab.uitest.TestCase% subclass of matlab.uitest.TestCase
    properties
        MainApp
        ValueChains
    end
    
    methods (TestMethodSetup)
        function launchApp(testCase)
            addpath(genpath('..\..\base_python'));
            addpath(genpath('..\..\base_matlab'));
            addpath(genpath('..\..\data'));
            testCase.MainApp = MainGUI(); % Get handle to Main App
            testCase.addTeardown(@delete,testCase.MainApp);
            testCase.ValueChains = testCase.MainApp.DropDown_ChooseWSK.Items; % all entries in the dropdown menue

            import matlab.unittest.constraints.IsGreaterThan
            import matlab.unittest.constraints.IsEqualTo
            
        end
    end
      
    
    methods (Test)
        function Run_single_BWK_A(testCase)
            testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,testCase.ValueChains{1});
            %Berechnung starten
            testCase.press(testCase.MainApp.BerechnungStartenButton);
            %Ergebnisse anzeigen:
            testCase.press(testCase.MainApp.ResultsButton);
            testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
            testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_SingleRun')
            testCase.MainApp.TearDown;
        end
        function Run_single_BWK_B(testCase)
            testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,testCase.ValueChains{2});
            %Berechnung starten
            testCase.press(testCase.MainApp.BerechnungStartenButton);
            %Ergebnisse anzeigen:
            testCase.press(testCase.MainApp.ResultsButton);
            testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
            testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_SingleRun')
            testCase.MainApp.TearDown;
        end
        function Run_single_BWK_C(testCase)
            testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,testCase.ValueChains{3});
            %Berechnung starten
            testCase.press(testCase.MainApp.BerechnungStartenButton);
            %Ergebnisse anzeigen:
            testCase.press(testCase.MainApp.ResultsButton);
            testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
            testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_SingleRun')
            testCase.MainApp.TearDown;
        end
        function Run_single_BWK_D(testCase)
            testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,testCase.ValueChains{4});
            %Berechnung starten
            testCase.press(testCase.MainApp.BerechnungStartenButton);
            %Ergebnisse anzeigen:
            testCase.press(testCase.MainApp.ResultsButton);
            testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
            testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_SingleRun')
            testCase.MainApp.TearDown;
        end


        
%         function CheckPropertyWindow(testCase)
%             testCase.choose(testCase.MainApp.ZielstellungDropDown,'Single Value Chain');
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'B Basic Demand');
%             
%             testCase.press(testCase.MainApp.ResultsButton);
%             
%             testCase.assertEqual(class(testCase.MainApp.PropertyWindow),'SzenarioPropertiesGUI')
%             geh durch alle Betriebsmodi
%             testCase.assertEqual(testCase.MainApp.PropertyWindow.TabGroup.SelectedTab, testCase.MainApp.PropertyWindow.KeyEconomicParameterTab);
%             
%             testCase.choose(testCase.MainApp.ZielstellungDropDown,'Sensitivity Analysis');
%             testCase.assertEqual(testCase.MainApp.PropertyWindow.TabGroup.SelectedTab, testCase.MainApp.PropertyWindow.ParameterOptimierungTab);
%             
%             testCase.choose(testCase.MainApp.ZielstellungDropDown,'Single Value Chain');
%             testCase.assertEqual(testCase.MainApp.PropertyWindow.TabGroup.SelectedTab, testCase.MainApp.PropertyWindow.KeyEconomicParameterTab);
%             
%             testCase.choose(testCase.MainApp.ZielstellungDropDown,'Regional Potential');
%             testCase.assertEqual(testCase.MainApp.PropertyWindow.TabGroup.SelectedTab, testCase.MainApp.PropertyWindow.KeyEconomicParameterTab);
%               
%             testCase.assertEqual(testCase.MainApp.PropertyWindowOpen,1)
%             testCase.press(testCase.MainApp.PropertyWindow.SpeichernundBeendenButton)
%             testCase.assertEqual(testCase.MainApp.PropertyWindowOpen,0)
%             testCase.MainApp.TearDown;
%         end
        
%         function TestingVLSfixed(testCase)
%             testCase.choose(testCase.MainApp.ZielstellungDropDown,'Berechnung des H2-Index');
%             % chose BWK
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'A CO2 Reduktion in der Industrie');
%             SubtestForVLSvariability()
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'B Basischemie');
%             SubtestForVLSvariability()
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'C Kraftstoffindustrie');
%             SubtestForVLSvariability()
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'D Erdgasnetz');
%             SubtestForVLSvariability()
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'E großtechn. Elektrolyse');
%             SubtestForVLSvariability()
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'F Power To Liquid');
%             SubtestForVLSvariability()
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'G Single Home');
%             SubtestForVLSvariability()
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'H Quartiersversorgung');
%             SubtestForVLSvariability()
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'I Tankstelle');
%             SubtestForVLSvariability2()% -- VLS initially NOT fixed
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'J Flottenversorgung');
%             SubtestForVLSvariability()
%             
%             testCase.MainApp.TearDown;
%             function SubtestForVLSvariability2()
%                 % change KPI
%                 testCase.press(testCase.MainApp.Button_Electrolyzer);
%                 testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_Electrolyzer')
%                 testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
%                 testCase.press(testCase.MainApp.Button_Electrolyzer);
%                 testCase.assertEqual(testCase.MainApp.KPIWindow.NachBedarfCheckBox.Value,false)
%                 testCase.press(testCase.MainApp.KPIWindow.NachBedarfCheckBox);
%                 testCase.assertEqual(testCase.MainApp.KPIWindow.NachBedarfCheckBox.Value,true)
%                 %testCase.MainApp.KPIWindow.TearDown();
%                 testCase.press(testCase.MainApp.KPIWindow.OKButton);
%                 testCase.assertEqual(testCase.MainApp.KPIWindowOpen,0)
%                 % run with VLS fixed:
%                 testCase.press(testCase.MainApp.BerechnungStartenButton);
%                 %% assert results of some kind here:
% 
%                 %% testrun with opposit checkbox value:
%                 testCase.press(testCase.MainApp.Button_Electrolyzer);
%                 testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_Electrolyzer')
%                 testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
%                 testCase.press(testCase.MainApp.Button_Electrolyzer);
%                 testCase.assertEqual(testCase.MainApp.KPIWindow.NachBedarfCheckBox.Value,true)
%                 testCase.press(testCase.MainApp.KPIWindow.NachBedarfCheckBox);
%                 testCase.assertEqual(testCase.MainApp.KPIWindow.NachBedarfCheckBox.Value,false)
%                 %testCase.MainApp.KPIWindow.TearDown();
%                 testCase.press(testCase.MainApp.KPIWindow.OKButton);
%                 testCase.assertEqual(testCase.MainApp.KPIWindowOpen,0)
%                 % run with VLS fixed:
%                 testCase.press(testCase.MainApp.BerechnungStartenButton);
%                 %% assert results of some kind here:
% 
%             end
%             function SubtestForVLSvariability()
%                 % change KPI
%                 testCase.press(testCase.MainApp.Button_Electrolyzer);
%                 testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_Electrolyzer')
%                 testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
%                 testCase.press(testCase.MainApp.Button_Electrolyzer);
%                 testCase.assertEqual(testCase.MainApp.KPIWindow.NachBedarfCheckBox.Value,true)
%                 testCase.press(testCase.MainApp.KPIWindow.NachBedarfCheckBox);
%                 testCase.assertEqual(testCase.MainApp.KPIWindow.NachBedarfCheckBox.Value,false)
%                 %testCase.MainApp.KPIWindow.TearDown();
%                 testCase.press(testCase.MainApp.KPIWindow.OKButton);
%                 testCase.assertEqual(testCase.MainApp.KPIWindowOpen,0)
%                 % run with VLS not fixed:
%                 testCase.press(testCase.MainApp.BerechnungStartenButton);
%                 %% assert results of some kind here:
%                 
%                 %% testrun with opposit checkbox value:
%                 testCase.press(testCase.MainApp.Button_Electrolyzer);
%                 testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_Electrolyzer')
%                 testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
%                 testCase.press(testCase.MainApp.Button_Electrolyzer);
%                 testCase.assertEqual(testCase.MainApp.KPIWindow.NachBedarfCheckBox.Value,false)
%                 testCase.press(testCase.MainApp.KPIWindow.NachBedarfCheckBox);
%                 testCase.assertEqual(testCase.MainApp.KPIWindow.NachBedarfCheckBox.Value,true)
%                 %testCase.MainApp.KPIWindow.TearDown();
%                 testCase.press(testCase.MainApp.KPIWindow.OKButton);
%                 testCase.assertEqual(testCase.MainApp.KPIWindowOpen,0)
%                 % run with VLS fixed:
%                 testCase.press(testCase.MainApp.BerechnungStartenButton);
%                 %% assert results of some kind here:
%                 
%             end
%         end
%         
%         function TestParameterSweep_twoparm(testCase)
%             testCase.choose(testCase.MainApp.ZielstellungDropDown,'Sensitivitätsanalyse');
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'C Kraftstoffindustrie');
%             testCase.press(testCase.MainApp.ResultsButton);
%             % Eigenschaftenfesnter geht auf
%             testCase.assertEqual(class(testCase.MainApp.PropertyWindow),'SzenarioPropertiesGUI')
%             % zeigt den richtigen Reiter
%             testCase.assertEqual(testCase.MainApp.PropertyWindow.TabGroup.SelectedTab, testCase.MainApp.PropertyWindow.ParameterOptimierungTab);
%             % chose to go only 2 steps in each direction
%             testCase.type(testCase.MainApp.PropertyWindow.AnzahlSchritteEditField_1,2);
%             testCase.type(testCase.MainApp.PropertyWindow.AnzahlSchritteEditField_2,2);
%             % Änderungen Annehmen:
%             testCase.press(testCase.MainApp.PropertyWindow.AnwendenButton);
%             % check ob Änderungen angenommen wurden
%             testCase.assertEqual(testCase.MainApp.Framework.ParameterSweep.Options.Parameter1.NumSteps,2)
%             testCase.assertEqual(testCase.MainApp.Framework.ParameterSweep.Options.Parameter2.NumSteps,2)
%             
%             % Berechnung starten
%             testCase.press(testCase.MainApp.BerechnungStartenButton);
%             % Ergebnisse anzeigen:
%             testCase.press(testCase.MainApp.ResultsButton);
%             testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
%             testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_ParameterSweep')
%             
%             % nochmal mit nur einem Parameter
%             testCase.press(testCase.MainApp.ResultsButton);
%             % Eigenschaftenfesnter geht auf
%             testCase.assertEqual(class(testCase.MainApp.PropertyWindow),'SzenarioPropertiesGUI')
%             % zeigt den richtigen Reiter
%             testCase.assertEqual(testCase.MainApp.PropertyWindow.TabGroup.SelectedTab, testCase.MainApp.PropertyWindow.ParameterOptimierungTab);
%             testCase.press(testCase.MainApp.PropertyWindow.ZweiParameterverwendenCheckBox)
%             % sollte jetzt nur noch einen Parameter verwendet
%             testCase.assertEqual(testCase.MainApp.PropertyWindow.ZweiParameterverwendenCheckBox.Value,false);
%             % Berechnung starten
%             testCase.press(testCase.MainApp.BerechnungStartenButton);
%             % Ergebnisse anzeigen:
%             testCase.press(testCase.MainApp.ResultsButton);
%             testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
%             testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_ParameterSweep')
%             testCase.MainApp.TearDown;
%         end
%         
% %         function TestRegionalCalculation(testCase)
% %             testCase.choose(testCase.MainApp.ZielstellungDropDown,'Regionale Standortoptimierung');
% %             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'J Flottenversorgung');
% %             % Berechnung starten
% %             testCase.press(testCase.MainApp.BerechnungStartenButton);
% %             % Ergebnisse anzeigen:
% %             testCase.press(testCase.MainApp.ResultsButton);
% %             testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
% %              testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_Regional')
% %             % close window:
% %             testCase.MainApp.ResultsWindow.TearDown()
% %             testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,0)
% %             testCase.MainApp.TearDown;
% %         end
%         
%         function TestPoliticalCalculation(testCase)
%             testCase.choose(testCase.MainApp.ZielstellungDropDown,'Evaluierung politischer Szenarien');
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'J Flottenversorgung');
%             testCase.press(testCase.MainApp.ResultsButton);
%             % Eigenschaftenfesnter geht auf
%             testCase.assertEqual(class(testCase.MainApp.PropertyWindow),'SzenarioPropertiesGUI')
%             % zeigt den richtigen Reiter
%             testCase.assertEqual(testCase.MainApp.PropertyWindow.TabGroup.SelectedTab, testCase.MainApp.PropertyWindow.politischeSzenarienTab);
%             % Berechnung starten
%             testCase.press(testCase.MainApp.BerechnungStartenButton);
%             % Ergebnisse anzeigen:
%             testCase.press(testCase.MainApp.ResultsButton);
%             testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
%             testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_Political')
%             testCase.MainApp.TearDown;
%         end
%         
%         function TestStorageMethod_PeakShaving(testCase)
%             testCase.choose(testCase.MainApp.ZielstellungDropDown,'Berechnung des H2-Index');
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'E großtechn. Elektrolyse');
%             % Storage Method setzten
%             testCase.press(testCase.MainApp.Button_Storage);
%             testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_Storage')
%             testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
%             testCase.choose(testCase.MainApp.KPIWindow.SpeicherzielDropDown,testCase.MainApp.KPIWindow.SpeicherzielDropDown.Items(1));% first is Peakshaving
%             testCase.assertEqual(testCase.MainApp.Framework.KPI.Storage.Method,'PeakShaving')
%             % Berechnung starten
%             testCase.press(testCase.MainApp.BerechnungStartenButton);
%             % Ergebnisse anzeigen:
%             testCase.press(testCase.MainApp.ResultsButton);
%             testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
%             testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_SingleRun')
%             
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'C Kraftstoffindustrie');
%             testCase.press(testCase.MainApp.BerechnungStartenButton);
%             testCase.press(testCase.MainApp.ResultsButton);
%             
%             testCase.MainApp.TearDown;
%         end
%         
%         function TestStorageMethod_MinContSupply(testCase)
%             testCase.choose(testCase.MainApp.ZielstellungDropDown,'Berechnung des H2-Index');
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'E großtechn. Elektrolyse');
%             % Storage Method setzten
%             testCase.press(testCase.MainApp.Button_Storage);
%             testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_Storage')
%             testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
%             testCase.choose(testCase.MainApp.KPIWindow.SpeicherzielDropDown,testCase.MainApp.KPIWindow.SpeicherzielDropDown.Items(2));% first is Peakshaving
%             testCase.assertEqual(testCase.MainApp.Framework.KPI.Storage.Method,'MinContSupply')
%             % Berechnung starten
%             testCase.press(testCase.MainApp.BerechnungStartenButton);
%             % Ergebnisse anzeigen:
%             testCase.press(testCase.MainApp.ResultsButton);
%             testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
%             testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_SingleRun')
%             
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'C Kraftstoffindustrie');
%             testCase.press(testCase.MainApp.BerechnungStartenButton);
%             testCase.press(testCase.MainApp.ResultsButton);
%             
%             testCase.MainApp.TearDown;
%         end
%         
%         function TestStorageMethod_Bandwidth(testCase)
%             testCase.choose(testCase.MainApp.ZielstellungDropDown,'Berechnung des H2-Index');
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'E großtechn. Elektrolyse');
%             % Storage Method setzten
%             testCase.press(testCase.MainApp.Button_Storage);
%             testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_Storage')
%             testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
%             testCase.choose(testCase.MainApp.KPIWindow.SpeicherzielDropDown,testCase.MainApp.KPIWindow.SpeicherzielDropDown.Items(3));% first is Peakshaving
%             testCase.assertEqual(testCase.MainApp.Framework.KPI.Storage.Method,'Bandwidth')
%             % Berechnung starten
%             testCase.press(testCase.MainApp.BerechnungStartenButton);
%             % Ergebnisse anzeigen:
%             testCase.press(testCase.MainApp.ResultsButton);
%             testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
%             testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_SingleRun')
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'C Kraftstoffindustrie');
%             testCase.press(testCase.MainApp.BerechnungStartenButton);
%             testCase.press(testCase.MainApp.ResultsButton);
%             testCase.MainApp.TearDown;
%             
%             
%         end
%         
%         function TestStorageMethod_Visibility(testCase)
%             testCase.choose(testCase.MainApp.ZielstellungDropDown,'Berechnung des H2-Index');
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,testCase.MainApp.DropDown_ChooseWSK.Items(10));
%             % Storage Method setzten
%             testCase.press(testCase.MainApp.Button_Storage);
%             testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_Storage')
%             testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
%             testCase.assertEqual(testCase.MainApp.KPIWindow.SpeicherzielDropDown.Visible,'off')
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,testCase.MainApp.DropDown_ChooseWSK.Items(5));
%             testCase.assertEqual(testCase.MainApp.KPIWindow.SpeicherzielDropDown.Visible,'on')
%             testCase.MainApp.TearDown;
%         end
%         
%         function TestGridParameters_I(testCase)
%             testCase.choose(testCase.MainApp.ZielstellungDropDown,'Berechnung des H2-Index');
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'I Tankstelle');
%             testCase.press(testCase.MainApp.Button_PowerGrid);
%             testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_GridParameters')
%             % in dieser BWK sollte die Stromnutzung editierbar sein
%             testCase.assertEqual(testCase.MainApp.KPIWindow.StromnutzungDropDown.Enable,'on')
%             testCase.assertEqual(testCase.MainApp.KPIWindow.MaximalpreisEditField.Enable,'on')
%             % nichtmehr sichtbar:
%             testCase.choose(testCase.MainApp.KPIWindow.QuelleDropDown,testCase.MainApp.KPIWindow.QuelleDropDown.Items(1)); % fester Arbeitspreis = erster Eintrag
%             testCase.assertEqual(testCase.MainApp.KPIWindow.StromnutzungDropDown.Enable,'off')
%             testCase.assertEqual(testCase.MainApp.KPIWindow.MaximalpreisEditField.Enable,'off')
%             
%             testCase.choose(testCase.MainApp.KPIWindow.QuelleDropDown,testCase.MainApp.KPIWindow.QuelleDropDown.Items(2)); % nach Strompreisprofil = zweiter Eintrag
%             testCase.assertEqual(testCase.MainApp.KPIWindow.StromnutzungDropDown.Enable,'on')
%             testCase.assertEqual(testCase.MainApp.KPIWindow.MaximalpreisEditField.Enable,'off')
%             % bis Grenzpreis erreicht:
%             testCase.choose(testCase.MainApp.KPIWindow.StromnutzungDropDown,testCase.MainApp.KPIWindow.StromnutzungDropDown.Items(2))% 1- ,aximal 2 - bis strompreis 3 - nach VLS ELY
%             testCase.assertEqual(testCase.MainApp.KPIWindow.MaximalpreisEditField.Enable,'on')
%             testCase.press(testCase.MainApp.BerechnungStartenButton);
%             % Ergebnisse anzeigen:
%             testCase.press(testCase.MainApp.ResultsButton);
%             testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
%             testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_SingleRun')
%             
%             % bis VLS erreicht:
%             testCase.choose(testCase.MainApp.KPIWindow.StromnutzungDropDown,testCase.MainApp.KPIWindow.StromnutzungDropDown.Items(3))
%             testCase.press(testCase.MainApp.BerechnungStartenButton);
%             % Ergebnisse anzeigen:
%             testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,0); % sollte mit Druckauf Start wieder zugegangen sein
%             testCase.press(testCase.MainApp.ResultsButton);
%             testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
%             testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_SingleRun')
%             
%             testCase.MainApp.TearDown;
%         end
%         
%         function TestGridParameters_C(testCase)
%             testCase.choose(testCase.MainApp.ZielstellungDropDown,'Berechnung des H2-Index');
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'C Kraftstoffindustrie');
%             testCase.press(testCase.MainApp.Button_PowerGrid);
%             testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_GridParameters')
%             % in dieser BWK sollte das Stromnutzung- Dropdown nicht editable sein
%             testCase.assertEqual(testCase.MainApp.KPIWindow.StromnutzungDropDown.Enable,'off')
%             % Editierbar machen:
%             testCase.choose(testCase.MainApp.KPIWindow.QuelleDropDown,testCase.MainApp.KPIWindow.QuelleDropDown.Items(2)); % nach Strompreisprofil = zweiter Eintrag
%             testCase.assertEqual(testCase.MainApp.KPIWindow.StromnutzungDropDown.Enable,'on')
%             %%  bis Grenzpreis erreicht:
%             testCase.choose(testCase.MainApp.KPIWindow.StromnutzungDropDown,testCase.MainApp.KPIWindow.StromnutzungDropDown.Items(1))
%             testCase.press(testCase.MainApp.BerechnungStartenButton);
%             % Ergebnisse anzeigen:
%             testCase.press(testCase.MainApp.ResultsButton);
%             testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
%             testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_SingleRun')
%             
%             %%  bis VLS erreicht:
%             testCase.choose(testCase.MainApp.KPIWindow.StromnutzungDropDown,testCase.MainApp.KPIWindow.StromnutzungDropDown.Items(1))
%             testCase.press(testCase.MainApp.BerechnungStartenButton);
%             % Ergebnisse anzeigen:
%             testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,0); % sollte mit Druckauf Start wieder zugegangen sein
%             testCase.press(testCase.MainApp.ResultsButton);
%             testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
%             testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_SingleRun')
%             % alles Schliessen
%             testCase.MainApp.TearDown;
%         end
%         
% %         function TestConverter_Options(testCase)
% %             testCase.choose(testCase.MainApp.ZielstellungDropDown,'Berechnung des H2-Index');
% %             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'F Power To Liquid');
% %             %% Optionen einstellen
% %             %TO DO
% %             
% %             testCase.press(testCase.MainApp.BerechnungStartenButton);
% %             % Ergebnisse anzeigen:
% %             testCase.press(testCase.MainApp.ResultsButton);
% %             
% %             testCase.MainApp.TearDown;
% %         end
%         
%         function TestCostoptions_Options(testCase)
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'K Freie Auswahl');
%             % set all buttons to enable:
%             %testCase.press(testCase.MainApp.DirectSupplyCheckBox) => wird mit 1 initialisiert 
%             testCase.assertEqual(testCase.MainApp.DirectSupplyCheckBox.Value,true)
%             testCase.press(testCase.MainApp.PowerGridCheckBox)
%             testCase.assertEqual(testCase.MainApp.PowerGridCheckBox.Value,true)
%             %testCase.press(testCase.MainApp.ElektrolyzerCheckBox)
%             %testCase.assertEqual(testCase.MainApp.ElektrolyzerCheckBox.Value,true)
%             testCase.press(testCase.MainApp.ConverterCheckBox)
%             testCase.assertEqual(testCase.MainApp.ConverterCheckBox.Value,true)
%             testCase.press(testCase.MainApp.StorageCheckBox)
%             testCase.assertEqual(testCase.MainApp.StorageCheckBox.Value,true)
%             testCase.press(testCase.MainApp.TransportCheckBox)
%             testCase.assertEqual(testCase.MainApp.TransportCheckBox.Value,true)
%             testCase.press(testCase.MainApp.ConsumerCheckBox)
%             testCase.assertEqual(testCase.MainApp.ConsumerCheckBox.Value,true)
%             
%             testCase.press(testCase.MainApp.DirectSupplyCheckBox)
%             testCase.assertEqual(testCase.MainApp.DirectSupplyCheckBox.Value,true)
%             testCase.press(testCase.MainApp.Button_PowerCreation);
%             testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_DirectEnergySupply')
%             testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
%             testCase.press(testCase.MainApp.KPIWindow.KostenBearbeitenButton); % öffnet Details der Kostenbestandteile
%             testCase.assertEqual(testCase.MainApp.KPIWindow.KostenWindowOpen,1);
%             testCase.press(testCase.MainApp.KPIWindow.KostenWindow.OKButton); % schliessen der Details der Kostenbestandteile
%             testCase.assertEqual(testCase.MainApp.KPIWindow.KostenWindowOpen,0);
%             
%             
%             testCase.press(testCase.MainApp.PowerGridCheckBox)
%             testCase.assertEqual(testCase.MainApp.PowerGridCheckBox.Value,true)
%             testCase.press(testCase.MainApp.Button_PowerGrid);
%             testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_GridParameters')
%             testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
%             
%             
%             testCase.press(testCase.MainApp.Button_Electrolyzer);
%             testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_Electrolyzer')
%             testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
%             testCase.press(testCase.MainApp.KPIWindow.KostenBearbeitenButton); % öffnet Details der Kostenbestandteile
%             testCase.assertEqual(testCase.MainApp.KPIWindow.KostenWindowOpen,1);
%             testCase.press(testCase.MainApp.KPIWindow.KostenWindow.OKButton); % schliessen der Details der Kostenbestandteile
%             testCase.assertEqual(testCase.MainApp.KPIWindow.KostenWindowOpen,0);
%             
%             
%             testCase.press(testCase.MainApp.Button_Transport);
%             testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_Transport')
%             testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
%             testCase.press(testCase.MainApp.KPIWindow.KostenBearbeitenButton); % öffnet Details der Kostenbestandteile
%             testCase.assertEqual(testCase.MainApp.KPIWindow.KostenWindowOpen,1);
%             testCase.press(testCase.MainApp.KPIWindow.KostenWindow.OKButton); % schliessen der Details der Kostenbestandteile
%             testCase.assertEqual(testCase.MainApp.KPIWindow.KostenWindowOpen,0);
%             
%             
%             testCase.press(testCase.MainApp.Button_Converter);
%             testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_Converter')
%             testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
%             testCase.press(testCase.MainApp.KPIWindow.KostenBearbeitenButton); % öffnet Details der Kostenbestandteile
%             testCase.assertEqual(testCase.MainApp.KPIWindow.KostenWindowOpen,1);
%             testCase.press(testCase.MainApp.KPIWindow.KostenWindow.OKButton); % schliessen der Details der Kostenbestandteile
%             testCase.assertEqual(testCase.MainApp.KPIWindow.KostenWindowOpen,0);
%             
%             testCase.press(testCase.MainApp.Button_Storage);
%             testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_Storage')
%             testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
%             testCase.press(testCase.MainApp.KPIWindow.KostenBearbeitenButton); % öffnet Details der Kostenbestandteile
%             testCase.assertEqual(testCase.MainApp.KPIWindow.KostenWindowOpen,1);
%             testCase.press(testCase.MainApp.KPIWindow.KostenWindow.OKButton); % schliessen der Details der Kostenbestandteile
%             testCase.assertEqual(testCase.MainApp.KPIWindow.KostenWindowOpen,0);
%             
%             testCase.press(testCase.MainApp.Button_Consumer);
%             testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_Consumer')
%             testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
%             
%             testCase.press(testCase.MainApp.Button_Transport);
%             testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_Transport')
%             testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
%             testCase.press(testCase.MainApp.KPIWindow.KostenBearbeitenButton); % öffnet Details der Kostenbestandteile
%             testCase.assertEqual(testCase.MainApp.KPIWindow.KostenWindowOpen,1);
%             testCase.press(testCase.MainApp.KPIWindow.KostenWindow.OKButton); % schliessen der Details der Kostenbestandteile
%             testCase.assertEqual(testCase.MainApp.KPIWindow.KostenWindowOpen,0);
%             
%             %Test beenden:
%             testCase.press(testCase.MainApp.KPIWindow.OKButton);
%             testCase.assertEqual(testCase.MainApp.KPIWindowOpen,0)
%             
%             testCase.MainApp.TearDown;
%         end
%         
%         
%         function TestingForAvailability_ELY(testCase)
%             testCase.choose(testCase.MainApp.ZielstellungDropDown,'Berechnung des H2-Index');
%             % chose BWK
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'A CO2 Reduktion in der Industrie');
%             SubtestForAvailability()
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'B Basischemie');
%             SubtestForAvailability()
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'C Kraftstoffindustrie');
%             SubtestForAvailability()
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'D Erdgasnetz');
%             SubtestForAvailability()
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'E großtechn. Elektrolyse');
%             SubtestForAvailability()
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'F Power To Liquid');
%             SubtestForAvailability()
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'G Single Home');
%             SubtestForAvailability()
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'H Quartiersversorgung');
%             SubtestForAvailability()
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'I Tankstelle');
%             SubtestForAvailability()
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'J Flottenversorgung');
%             SubtestForAvailability()
%             
%             testCase.MainApp.TearDown;
%             
%             function SubtestForAvailability()
%                 % change KPI
%                 testCase.press(testCase.MainApp.Button_Electrolyzer);
%                 testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_Electrolyzer')
%                 testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
%                 testCase.press(testCase.MainApp.Button_Electrolyzer);
%                 if testCase.MainApp.Framework.KPI.Electrolyzer.AvailabilityFixed
%                     testCase.assertEqual(testCase.MainApp.KPIWindow.WartungeinplanenCheckBox.Value,true)
%                     testCase.press(testCase.MainApp.KPIWindow.WartungeinplanenCheckBox);
%                     testCase.assertEqual(testCase.MainApp.KPIWindow.WartungeinplanenCheckBox.Value,false)
%                 else
%                     testCase.assertEqual(testCase.MainApp.KPIWindow.WartungeinplanenCheckBox.Value,false)
%                     testCase.press(testCase.MainApp.KPIWindow.WartungeinplanenCheckBox);
%                     testCase.assertEqual(testCase.MainApp.KPIWindow.WartungeinplanenCheckBox.Value,true)
%                     testCase.press(testCase.MainApp.KPIWindow.WartungeinplanenCheckBox);
%                 end
%                 %testCase.MainApp.KPIWindow.TearDown();
%                 testCase.press(testCase.MainApp.KPIWindow.OKButton);
%                 testCase.assertEqual(testCase.MainApp.KPIWindowOpen,0)
%                 % run with VLS not fixed:
%                 testCase.press(testCase.MainApp.BerechnungStartenButton);
%                 
%                 %% testrun with opposit checkbox value:
%                 testCase.press(testCase.MainApp.Button_Electrolyzer);
%                 testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_Electrolyzer')
%                 testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
%                 testCase.press(testCase.MainApp.Button_Electrolyzer);
%                 testCase.assertEqual(testCase.MainApp.KPIWindow.WartungeinplanenCheckBox.Value,false)
%                 testCase.press(testCase.MainApp.KPIWindow.WartungeinplanenCheckBox);
%                 testCase.assertEqual(testCase.MainApp.KPIWindow.WartungeinplanenCheckBox.Value,true)
%                 %testCase.MainApp.KPIWindow.TearDown();
%                 testCase.press(testCase.MainApp.KPIWindow.OKButton);
%                 testCase.assertEqual(testCase.MainApp.KPIWindowOpen,0)
%                 % run with VLS fixed:
%                 testCase.press(testCase.MainApp.BerechnungStartenButton);               
%             end
%         end
%         
%         function TestingForAvailability_Converter(testCase)
%             testCase.choose(testCase.MainApp.ZielstellungDropDown,'Berechnung des H2-Index');
%             % chose BWK
%             testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'F Power To Liquid');
%             SubtestForAvailability()
%             testCase.MainApp.TearDown;
%             
%             function SubtestForAvailability()
%                 % change KPI
%                 testCase.press(testCase.MainApp.Button_Converter);
%                 testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_Converter')
%                 testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
%                 testCase.press(testCase.MainApp.Button_Converter);
%                 testCase.assertEqual(testCase.MainApp.KPIWindow.WartungeinplanenCheckBox.Value,true)
%                 testCase.press(testCase.MainApp.KPIWindow.WartungeinplanenCheckBox);
%                 testCase.assertEqual(testCase.MainApp.KPIWindow.WartungeinplanenCheckBox.Value,false)
%                 testCase.press(testCase.MainApp.KPIWindow.OKButton);
%                 testCase.assertEqual(testCase.MainApp.KPIWindowOpen,0)
%                 % run with VLS not fixed:
%                 testCase.press(testCase.MainApp.BerechnungStartenButton);
%                 
%                 %% testrun with opposit checkbox value:
%                 testCase.press(testCase.MainApp.Button_Converter);
%                 testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_Converter')
%                 testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
%                 testCase.press(testCase.MainApp.Button_Converter);
%                 testCase.assertEqual(testCase.MainApp.KPIWindow.WartungeinplanenCheckBox.Value,false)
%                 testCase.press(testCase.MainApp.KPIWindow.WartungeinplanenCheckBox);
%                 testCase.assertEqual(testCase.MainApp.KPIWindow.WartungeinplanenCheckBox.Value,true)
%                 testCase.press(testCase.MainApp.KPIWindow.OKButton);
%                 testCase.assertEqual(testCase.MainApp.KPIWindowOpen,0)
%                 % run with VLS fixed:
%                 testCase.press(testCase.MainApp.BerechnungStartenButton);               
%             end
%         end
       
    end
end


