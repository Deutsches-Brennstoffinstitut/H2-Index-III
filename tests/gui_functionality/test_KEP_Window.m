classdef test_KEP_Window < matlab.uitest.TestCase% subclass of matlab.uitest.TestCase
    properties
        MainApp                                 % will hold the GUI Framework
        ValueChains                             % entries to the Value chain drop down menue
        Window_Name = 'test_KEP_Window';   % the KPI Window for which these tests are relevant
        list_of_valuechains = [1, 2, 3, 4];              % list ov Value chains ID#s where this window is relevant
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
        function Renewables(testCase) 
            % set up Main GUI
            testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
            % test opening and closing for each relevant Value chain:
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,testCase.ValueChains{testCase.list_of_valuechains(1)}); % BWK A
            testCase.assertEqual(testCase.MainApp.DirectSupplyCheckBox.Value,true)
            % open the KPI Window
            testCase.press(testCase.MainApp.Button_PowerCreation);
            %% press button: Cost Options
            testCase.press(testCase.MainApp.KPIWindow.KostenBearbeitenButton);
            % check default value: use database values = true
            testCase.assertEqual(testCase.MainApp.KPIWindow.KostenWindow.UseDatabaseValuesCheckBox.Value, true);

            %% close window
                
            testCase.MainApp.TearDown;
        end
        
        function Grid(testCase) 
            % set up Main GUI
            testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
            % test opening and closing for each relevant Value chain:
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,testCase.ValueChains{testCase.list_of_valuechains(1)}); % BWK B
            testCase.assertEqual(testCase.MainApp.PowerGridCheckBox.Value,true)
            % open the KPI Window
            testCase.press(testCase.MainApp.Button_PowerGrid);
            %% Cost options for Grid are different..... test here:

            %% close window
                
            testCase.MainApp.TearDown;
        end

        function Electrolyzer(testCase) 
            % set up Main GUI
            testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
            % test opening and closing for each relevant Value chain:
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,testCase.ValueChains{testCase.list_of_valuechains(1)}); % BWK A
            %testCase.assertEqual(testCase.MainApp.DirectSupplyCheckBox.Value,true)
            % open the KPI Window
            testCase.press(testCase.MainApp.Button_Electrolyzer);
            %% press button: Cost Options
            testCase.press(testCase.MainApp.KPIWindow.KostenBearbeitenButton);
            % check default value: use database values = true
            testCase.assertEqual(testCase.MainApp.KPIWindow.KostenWindow.UseDatabaseValuesCheckBox.Value, true);

            %% close all windows
            testCase.MainApp.TearDown;
        end

        function Storage(testCase) 
            % set up Main GUI
            testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
            % test opening and closing for each relevant Value chain:
            %testCase.choose(testCase.MainApp.DropDown_ChooseWSK,testCase.ValueChains{testCase.list_of_valuechains(1)}); % BWK A
            %testCase.assertEqual(testCase.MainApp.DirectSupplyCheckBox.Value,true)
            % open the KPI Window
            testCase.press(testCase.MainApp.Button_PowerCreation);
            %% press button: Cost Options
            testCase.press(testCase.MainApp.KPIWindow.KostenBearbeitenButton);
            % check default value: use database values = true
            testCase.assertEqual(testCase.MainApp.KPIWindow.KostenWindow.UseDatabaseValuesCheckBox.Value, true);

            %% close window
                
            testCase.MainApp.TearDown;
        end
        function Methanation(testCase) 
            % set up Main GUI
            testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
            % test opening and closing for each relevant Value chain:
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,testCase.ValueChains{testCase.list_of_valuechains(3)}); % BWK C
            testCase.assertEqual(testCase.MainApp.ConverterCheckBox.Value,true)
            % open the KPI Window
            testCase.press(testCase.MainApp.Button_Converter);
            %% press button: Cost Options
            testCase.press(testCase.MainApp.KPIWindow.KostenBearbeitenButton);
            % check default value: use database values = true
            testCase.assertEqual(testCase.MainApp.KPIWindow.KostenWindow.UseDatabaseValuesCheckBox.Value, true);

            %% close window
                
            testCase.MainApp.TearDown;
        end
        function Transport(testCase) 
            % set up Main GUI
            testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
            % test opening and closing for each relevant Value chain:
            testCase.choose(testCase.MainApp.DropDown_ChooseWSK,testCase.ValueChains{testCase.list_of_valuechains(4)}); % BWK D
            testCase.assertEqual(testCase.MainApp.TransportCheckBox.Value,true)
            % open the KPI Window
            testCase.press(testCase.MainApp.Button_Transport);
            %% press button: Cost Options
            testCase.press(testCase.MainApp.KPIWindow.KostenBearbeitenButton);
            % check default value: use database values = true
            testCase.assertEqual(testCase.MainApp.KPIWindow.KostenWindow.UseDatabaseValuesCheckBox.Value, true);

            %% close window
                
            testCase.MainApp.TearDown;
        end
     

    end
end


