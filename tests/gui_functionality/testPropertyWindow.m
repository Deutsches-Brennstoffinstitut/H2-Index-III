
classdef testPropertyWindow < matlab.uitest.TestCase% subclass of matlab.uitest.TestCase
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
    
    methods (Test)
        
        function PropertyWindow_SingleRun(testCase)
            testCase.choose(testCase.MainApp.ZielstellungDropDown,'Berechnung des H2-Index');
            
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'A CO2 Reduktion in der Industrie');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'B Basischemie');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'C Kraftstoffindustrie');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'D Erdgasnetz');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'E großtechn. Elektrolyse');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'F Power To Liquid');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'G Single Home');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'H Quartiersversorgung');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'I Tankstelle');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'J Flottenversorgung');
            checkPropertyWindow()
            testCase.MainApp.TearDown;
            
            function checkPropertyWindow()
                % öffne Eigenschaftenfenster
                testCase.press(testCase.MainApp.ResultsButton);
                % Eigenschaftenfesnter geht auf
                testCase.assertEqual(testCase.MainApp.PropertyWindowOpen,1)
                testCase.assertEqual(class(testCase.MainApp.PropertyWindow),'SzenarioPropertiesGUI')
                % zeigt den richtigen Reiter
                testCase.assertEqual(testCase.MainApp.PropertyWindow.TabGroup.SelectedTab, testCase.MainApp.PropertyWindow.KeyEconomicParameterTab);
                testCase.press(testCase.MainApp.PropertyWindow.SpeichernundBeendenButton)
                testCase.assertEqual(testCase.MainApp.PropertyWindowOpen,0)
            end
        end
        
        
        function PropertyWindow_ParamterSweep(testCase)
            testCase.choose(testCase.MainApp.ZielstellungDropDown,'Sensitivitätsanalyse');
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'A CO2 Reduktion in der Industrie');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'B Basischemie');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'C Kraftstoffindustrie');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'D Erdgasnetz');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'E großtechn. Elektrolyse');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'F Power To Liquid');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'G Single Home');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'H Quartiersversorgung');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'I Tankstelle');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'J Flottenversorgung');
            checkPropertyWindow()
            testCase.MainApp.TearDown;
            
            function checkPropertyWindow()
                % öffne Eigenschaftenfenster
                testCase.press(testCase.MainApp.ResultsButton);
                % Eigenschaftenfesnter geht auf
                testCase.assertEqual(testCase.MainApp.PropertyWindowOpen,1)
                testCase.assertEqual(class(testCase.MainApp.PropertyWindow),'SzenarioPropertiesGUI')
                % zeigt den richtigen Reiter
                testCase.assertEqual(testCase.MainApp.PropertyWindow.TabGroup.SelectedTab, testCase.MainApp.PropertyWindow.ParameterOptimierungTab);
                testCase.press(testCase.MainApp.PropertyWindow.SpeichernundBeendenButton)
                testCase.assertEqual(testCase.MainApp.PropertyWindowOpen,0)
            end
        end
        
        function PropertyWindow_Political(testCase)
            testCase.choose(testCase.MainApp.ZielstellungDropDown,'Evaluierung politischer Szenarien');
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'A CO2 Reduktion in der Industrie');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'B Basischemie');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'C Kraftstoffindustrie');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'D Erdgasnetz');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'E großtechn. Elektrolyse');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'F Power To Liquid');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'G Single Home');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'H Quartiersversorgung');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'I Tankstelle');
            checkPropertyWindow()
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,'J Flottenversorgung');
            checkPropertyWindow()
            testCase.MainApp.TearDown;
            
            function checkPropertyWindow()
                % öffne Eigenschaftenfenster
                testCase.press(testCase.MainApp.ResultsButton);
                % Eigenschaftenfesnter geht auf
                testCase.assertEqual(testCase.MainApp.PropertyWindowOpen,1)
                testCase.assertEqual(class(testCase.MainApp.PropertyWindow),'SzenarioPropertiesGUI')
                % zeigt den richtigen Reiter
                testCase.assertEqual(testCase.MainApp.PropertyWindow.TabGroup.SelectedTab, testCase.MainApp.PropertyWindow.politischeSzenarienTab);
                testCase.press(testCase.MainApp.PropertyWindow.SpeichernundBeendenButton)
                testCase.assertEqual(testCase.MainApp.PropertyWindowOpen,0)
            end
        end
       
        
    end
end