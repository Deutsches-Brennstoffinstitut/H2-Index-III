%Ausführen:
%results = runtests('TestingH2Tool')
%Parallel:
%results = runtests('TestingH2Tool','UseParallel',true)

classdef test_KPIWindow_Grid < matlab.uitest.TestCase% subclass of matlab.uitest.TestCase
    properties
        MainApp                                 % will hold the GUI Framework
        ValueChains                             % entries to the Value chain drop down menue
        Window_Name = 'KPIWindow_Grid';     % the KPI Window for which these tests are relevant
        list_of_valuechains = 2 ;     % list ov Value chains ID#s where this window is relevant
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
            % after opening the window, BWK A should be initialized:
            % open and Close the Window without selscting the value chain:
            open_close_KPI_Window(testCase, testCase.Window_Name, testCase.MainApp.Button_PowerGrid);
            % test opening and closing for each relevant Value chain:
            for Index = 1:numel(testCase.list_of_valuechains)
                % disp(Drop_down_entry)
                testCase.choose(testCase.MainApp.DropDown_ChooseWSK, testCase.ValueChains{testCase.list_of_valuechains(Index)});
                % open and Close the Window
                open_close_KPI_Window(testCase, testCase.Window_Name, testCase.MainApp.Button_PowerGrid);
            end
            testCase.MainApp.TearDown;
        end

%         function load_profile(testCase)
%             import matlab.mock.actions.AssignOutputs
%             % set up Main GUI
%             testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
%             % test opening and closing for each relevant Value chain:
%             for Index = 1:numel(testCase.list_of_valuechains)
%                 Drop_down_entry = testCase.ValueChains{testCase.list_of_valuechains(Index)}; % indes is only number of entry (which then gives the number of value chain)
%                 testCase.choose(testCase.MainApp.DropDown_ChooseWSK, Drop_down_entry);
% 
%                 % open and Close the Window
%                 testCase.press(testCase.MainApp.Button_Consumer);
%                 %testCase.MainApp.KPIWindow.LoadProfileButtonTest('..\test_profiles\03_with_errors.xlsx'); % --> should not load file, but sdhould also not crassh the GUI
%                 
%                 testCase.MainApp.KPIWindow.LoadProfileButtonTest('..\test_profiles\04_constant.xlsx');
% 
%                 %Berechnung starten
%                 testCase.press(testCase.MainApp.BerechnungStartenButton);
%                 %Ergebnisse anzeigen:
%                 testCase.press(testCase.MainApp.ResultsButton);
%                 testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
% 
%             end
%             testCase.MainApp.TearDown;
%         end
% 
%         function set_profile(testCase)
%             % set up Main GUI
%             testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
%             % test for each relevant Value chain:
%             for Index = testCase.list_of_valuechains
%                 Drop_down_entry_WSK = testCase.ValueChains{Index}; % indes is  number of  value chain)
%                 disp(Drop_down_entry_WSK)
%                 testCase.choose(testCase.MainApp.DropDown_ChooseWSK, Drop_down_entry_WSK);
% 
%                 % open and Close the Window
%                 testCase.press(testCase.MainApp.Button_Consumer);
%                 testCase.verifyEqual(...
%                     testCase.MainApp.KPIWindow.ScalingkWhaEditField.Value, ...
%                     sum(testCase.MainApp.Profile.Consumer.H2_Demand_kWh  ));
% 
%                 for Drop_down_entry = testCase.MainApp.KPIWindow.IndustryProfiles.Items
%                     disp([Drop_down_entry_WSK, Drop_down_entry])
%                     testCase.press(testCase.MainApp.Button_Consumer);
%                     testCase.choose(testCase.MainApp.KPIWindow.IndustryProfiles, Drop_down_entry);
%                     testCase.verifyEqual(...
%                         testCase.MainApp.KPIWindow.ScalingkWhaEditField.Value, ...
%                         sum(testCase.MainApp.Profile.Consumer.H2_Demand_kWh));
% 
%                     %Berechnung starten
%                     testCase.press(testCase.MainApp.BerechnungStartenButton);
%                     %Ergebnisse anzeigen:
%                     testCase.press(testCase.MainApp.ResultsButton);
%                     testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
%                 end
%             end
%             testCase.MainApp.TearDown;
%         end
        
    end
end


