%Ausführen:
%results = runtests('TestingH2Tool')
%Parallel:
%results = runtests('TestingH2Tool','UseParallel',true)

classdef test_KPIWindow_Transport < matlab.uitest.TestCase% subclass of matlab.uitest.TestCase
    properties
        MainApp                                 % will hold the GUI Framework
        ValueChains                             % entries to the Value chain drop down menue
        Window_Name = 'KPIWindow_Transport';   % the KPI Window for which these tests are relevant
        list_of_valuechains = [3, 4];              % list ov Value chains ID#s where this window is relevant
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
                testCase.choose(testCase.MainApp.DropDown_ChooseWSK, testCase.ValueChains{testCase.list_of_valuechains(Index)});
                % open and Close the Window
                open_close_KPI_Window(testCase, testCase.Window_Name, testCase.MainApp.Button_Transport);
            end
            testCase.MainApp.TearDown;
        end

        function zero_nominal_power(testCase)
            % set up Main GUI
            testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
            % test opening and closing for each relevant Value chain:
            for Index = 1:numel(testCase.list_of_valuechains)
                Drop_down_entry = testCase.ValueChains{testCase.list_of_valuechains(Index)}; % indes is only number of entry (which then gives the number of value chain)
                testCase.choose(testCase.MainApp.DropDown_ChooseWSK, Drop_down_entry);

                % open and Close the Window
                testCase.press(testCase.MainApp.Button_PowerCreation);
                %% set PV + Wind Power to Zero
                %app.ParentFramework.Framework.KPI.EnergySupply.Wind_NominalPower     
                %testCase.type(testCase.MainApp.KPIWindow.NennleistungEditField, 0) % set True
%                 %app.ParentFramework.Framework.KPI.EnergySupply.PV_NominalPower 
%                 testCase.type(testCase.MainApp.KPIWindow.UITableStromAnlagen, [2,2], "0") % set True
%                 
%                 %Berechnung starten
%                 testCase.press(testCase.MainApp.BerechnungStartenButton);
%                 %Ergebnisse anzeigen:
%                 testCase.press(testCase.MainApp.ResultsButton);
%                 testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
%                 testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_SingleRun')
%                 
%                 % --> results should show no CAPEX for RE
%                 testCase.assertEqual(testCase.MainApp.ResultsWindow.CAPEXEditField.Value, 0)
% 
%                 % --> results should show no produced Power
%                 testCase.assertEqual(testCase.MainApp.ResultsWindow.CAPEXEditField.Value, 0)
% 
%                 % --> results should show no produced Hydrogen
%                 testCase.assertEqual(testCase.MainApp.ResultsWindow.CAPEXEditField.Value, 0)
% 
%                 % --> no Cost for Production of Power
%                 testCase.assertEqual(testCase.MainApp.ResultsWindow.CAPEXEditField.Value, 0)

            end
            testCase.MainApp.TearDown;
        end

        
    end
end


