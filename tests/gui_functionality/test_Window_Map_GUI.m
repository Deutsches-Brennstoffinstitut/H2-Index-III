classdef test_Window_Map_GUI < matlab.uitest.TestCase% subclass of matlab.uitest.TestCase
    properties
        MainApp                                 % will hold the GUI Framework
        ValueChains                             % entries to the Value chain drop down menue
        Window_Name = 'test_Window_Map_GUI';   % the KPI Window for which these tests are relevant
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
            % set up Main GUI
            testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
            % test opening and closing for each relevant Value chain:
            for Index = 1:numel(testCase.list_of_valuechains)
                % Drop_down_entry = testCase.ValueChains{testCase.list_of_valuechains(Index)}; % indes is only number of entry (which then gives the number of value chain)
                % disp(Drop_down_entry)
                testCase.choose(testCase.MainApp.DropDown_ChooseWSK,testCase.ValueChains{testCase.list_of_valuechains(Index)});
                testCase.assertEqual(testCase.MainApp.DirectSupplyCheckBox.Value,true)
                % open and Close the Window
                testCase.press(testCase.MainApp.Button_PowerCreation);
                
                %% press button: oprn window, close window, 
                %%get_Map_GUI_profile

                
            end
            testCase.MainApp.TearDown;
        end
        
        function read(testCase)
            % set up Main GUI
            testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
            % test opening and closing for each relevant Value chain:
            for Index = 1:numel(testCase.list_of_valuechains)
                Drop_down_entry = testCase.ValueChains{testCase.list_of_valuechains(Index)}; % indes is only number of entry (which then gives the number of value chain)
                testCase.choose(testCase.MainApp.DropDown_ChooseWSK, Drop_down_entry);
                testCase.assertEqual(testCase.MainApp.DirectSupplyCheckBox.Value,true)
                % open the KPI Window
                testCase.press(testCase.MainApp.Button_PowerCreation);
                %% press button: oprn window, close window, 
                % get_Map_GUI_profile


                %% do some magic
                

            end
            testCase.MainApp.TearDown;
        end

        
    end
end


