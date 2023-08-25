
classdef testParameterSweep < matlab.uitest.TestCase% subclass of matlab.uitest.TestCase
    properties
        MainApp
    end
    
    methods (TestMethodSetup)
        function launchApp(testCase)
            addpath(genpath('..\..\GUI'));
            addpath(genpath('..\..\Functions'));
            addpath(genpath('..\..\Data'));
            testCase.MainApp = MainGUI(); % Get handle to Main App
            testCase.addTeardown(@delete,testCase.MainApp);
        end
    end
    
    
    
    methods (Access = private)
        
        function Setup(testCase)
            testCase.choose(testCase.MainApp.ZielstellungDropDown,'Sensitivitätsanalyse');%app.ZielstellungDropDown.Items(2)
            %% set VLS fixed (initial sweep parameters are size and VLS)
            testCase.press(testCase.MainApp.Button_Electrolyzer);
            testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_Electrolyzer')
            testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
            testCase.press(testCase.MainApp.KPIWindow.NachBedarfCheckBox)
            testCase.assertEqual(testCase.MainApp.Framework.KPI.Electrolyzer.VLSfixed, 'on');
            testCase.press(testCase.MainApp.KPIWindow.WartungeinplanenCheckBox);
            testCase.assertEqual(testCase.MainApp.Framework.KPI.Electrolyzer.AvailabilityFixed, 'off');
            testCase.press(testCase.MainApp.KPIWindow.OKButton);
            testCase.assertEqual(testCase.MainApp.KPIWindowOpen,0)
        end
        
        function TestParameterSweep_main(testCase)
            %testCase.choose(testCase.MainApp.ZielstellungDropDown,'Sensitivitätsanalyse');
            testCase.press(testCase.MainApp.ResultsButton);
            % Eigenschaftenfesnter geht auf
            testCase.assertEqual(class(testCase.MainApp.PropertyWindow),'SzenarioPropertiesGUI')
            % zeigt den richtigen Reiter
            testCase.assertEqual(testCase.MainApp.PropertyWindow.TabGroup.SelectedTab, testCase.MainApp.PropertyWindow.ParameterOptimierungTab);
            % check ob ein oder Zwei Parameter eingeschaltet sind
            if testCase.MainApp.Framework.ParameterSweep.Options.SingleParameterSweepIndicator
                %schalte double Paramter sweep ein
                testCase.press(testCase.MainApp.PropertyWindow.ZweiParameterverwendenCheckBox)
                testCase.assertEqual(testCase.MainApp.PropertyWindow.ZweiParameterverwendenCheckBox.Value,true);
                testCase.press(testCase.MainApp.PropertyWindow.AnwendenButton);
                testCase.assertEqual(testCase.MainApp.Framework.ParameterSweep.Options.SingleParameterSweepIndicator,false);
            end
            
            % chose to go only 2 steps in each direction
            testCase.type(testCase.MainApp.PropertyWindow.AnzahlSchritteEditField_1,2);
            testCase.type(testCase.MainApp.PropertyWindow.AnzahlSchritteEditField_2,2);
            % Änderungen Annehmen:
            testCase.press(testCase.MainApp.PropertyWindow.AnwendenButton);
            % check ob Änderungen angenommen wurden
            testCase.assertEqual(testCase.MainApp.Framework.ParameterSweep.Options.Parameter1.NumSteps,2)
            testCase.assertEqual(testCase.MainApp.Framework.ParameterSweep.Options.Parameter2.NumSteps,2)
            
            % Berechnung starten
            testCase.press(testCase.MainApp.BerechnungStartenButton);
            % Ergebnisse anzeigen:
            testCase.press(testCase.MainApp.ResultsButton);
            testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
            testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_ParameterSweep')
            % close window:
            testCase.MainApp.ResultsWindow.TearDown()
            testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,0)
            
            % nochmal mit nur einem Parameter
            testCase.press(testCase.MainApp.ResultsButton);
            % Eigenschaftenfesnter geht auf
            testCase.assertEqual(class(testCase.MainApp.PropertyWindow),'SzenarioPropertiesGUI')
            % zeigt den richtigen Reiter
            testCase.assertEqual(testCase.MainApp.PropertyWindow.TabGroup.SelectedTab, testCase.MainApp.PropertyWindow.ParameterOptimierungTab);
            testCase.press(testCase.MainApp.PropertyWindow.ZweiParameterverwendenCheckBox)
            % sollte jetzt nur noch einen Parameter verwendet
            testCase.assertEqual(testCase.MainApp.PropertyWindow.ZweiParameterverwendenCheckBox.Value,false);
            testCase.press(testCase.MainApp.PropertyWindow.AnwendenButton);
            % Berechnung starten
            testCase.press(testCase.MainApp.BerechnungStartenButton);
            % Ergebnisse anzeigen:
            testCase.press(testCase.MainApp.ResultsButton);
            testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
            testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_ParameterSweep')
            % close window:
            testCase.MainApp.ResultsWindow.TearDown()
            testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,0)
        end
        
    end
    
    methods (Test)
        function RunBWK_A(testCase)
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'A CO2 Reduktion in der Industrie');
            Setup(testCase)
            TestParameterSweep_main(testCase)
            testCase.MainApp.TearDown;
        end
        
        function RunBWK_B(testCase)
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'B Basischemie');
            Setup(testCase)
            TestParameterSweep_main(testCase)
            testCase.MainApp.TearDown;
            
        end
        function RunBWK_C(testCase)
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'C Kraftstoffindustrie');
            Setup(testCase)
            TestParameterSweep_main(testCase)
            testCase.MainApp.TearDown;
            
        end
        function RunBWK_D(testCase)
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'D Erdgasnetz');
            testCase.press(testCase.MainApp.Button_PowerCreation);
            testCase.assertEqual(class(testCase.MainApp.KPIWindow),'KPIWindow_DirectEnergySupply')
            testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
            testCase.press(testCase.MainApp.KPIWindow.OKButton);
            testCase.assertEqual(testCase.MainApp.KPIWindowOpen,0)
            Setup(testCase)
            TestParameterSweep_main(testCase)
            testCase.MainApp.TearDown;
            
        end
        function RunBWK_E(testCase)
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'E großtechn. Elektrolyse');
            Setup(testCase)
            TestParameterSweep_main(testCase)
            testCase.MainApp.TearDown;
            
        end
        function RunBWK_F(testCase)
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'F Power To Liquid');
            Setup(testCase)
            TestParameterSweep_main(testCase)
            testCase.MainApp.TearDown;
        end
        function RunBWK_G(testCase)
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'G Single Home');
            Setup(testCase)
            TestParameterSweep_main(testCase)
            testCase.MainApp.TearDown;
        end
        function RunBWK_H(testCase)
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'H Quartiersversorgung');
            Setup(testCase)
            TestParameterSweep_main(testCase)
            testCase.MainApp.TearDown;
        end
        function RunBWK_I(testCase)
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'I Tankstelle');
            Setup(testCase)
            TestParameterSweep_main(testCase)
            testCase.MainApp.TearDown;
        end
        function RunBWK_J(testCase)
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'J Flottenversorgung');
            Setup(testCase)
            TestParameterSweep_main(testCase)
            testCase.MainApp.TearDown;
        end
    end
end


