%Ausführen:
%results = runtests('TestingH2Tool')
%Parallel:
%results = runtests('TestingH2Tool','UseParallel',true)

classdef test_KPIWindow_Storage < matlab.uitest.TestCase% subclass of matlab.uitest.TestCase
    properties
        MainApp                                 % will hold the GUI Framework
        ValueChains                             % entries to the Value chain drop down menue
        Window_Name = 'KPIWindow_Storage';   % the KPI Window for which these tests are relevant
        list_of_valuechains = [2, 4];              % list ov Value chains ID#s where this window is relevant
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
                % disp(Drop_down_entry)
                testCase.choose(testCase.MainApp.DropDown_ChooseWSK, testCase.ValueChains{testCase.list_of_valuechains(Index)});
                % open and Close the Window
                open_close_KPI_Window(testCase, testCase.Window_Name, testCase.MainApp.Button_Storage);
            end
            testCase.MainApp.TearDown;
        end

        function zero_capacity(testCase)
            % set up Main GUI
            testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
            % test opening and closing for each relevant Value chain:
            for Index = 1:numel(testCase.list_of_valuechains)
                Drop_down_entry = testCase.ValueChains{testCase.list_of_valuechains(Index)}; % indes is only number of entry (which then gives the number of value chain)
                testCase.choose(testCase.MainApp.DropDown_ChooseWSK, Drop_down_entry);

                % open and Close the Window
                testCase.press(testCase.MainApp.Button_Storage);
                %% set PV + Wind Power to Zero
                testCase.type(testCase.MainApp.KPIWindow.CapacitykgEditField, 0)
                testCase.type(testCase.MainApp.KPIWindow.InitialFillingkgEditField, 0) 

                %Berechnung starten
                testCase.press(testCase.MainApp.BerechnungStartenButton);
                %Ergebnisse anzeigen:
                testCase.press(testCase.MainApp.ResultsButton);
                testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
                testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_SingleRun')
                % no capcity installed
                testCase.assertEqual(testCase.MainApp.ResultsWindow.CapacitykgEditField.Value, 0)
                %  no Costs
                testCase.assertEqual(testCase.MainApp.ResultsWindow.InvestitionskostenEditField_H2Tank.Value, 0)
                % --> No Costs
                testCase.assertEqual(testCase.MainApp.ResultsWindow.BetriebskostenEditField_H2Tank.Value, 0)

            end
            testCase.MainApp.TearDown;
        end

        
    end
end


