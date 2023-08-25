%Ausführen:
%results = runtests('TestingH2Tool')
%Parallel:
%results = runtests('TestingH2Tool','UseParallel',true)

classdef test_KPIWindow_Ely < matlab.uitest.TestCase% subclass of matlab.uitest.TestCase
    properties
        MainApp                                 % will hold the GUI Framework
        ValueChains                             % entries to the Value chain drop down menue
        Window_Name = 'KPIWindow_Electrolyzer';   % the KPI Window for which these tests are relevant
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
        function open_and_close(testCase)
            % set up Main GUI
            testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
            % after opening the window, BWK A should be initialized:
            % open and Close the Window
            open_close_KPI_Window(testCase, testCase.Window_Name, testCase.MainApp.Button_Electrolyzer);

            % test opening and closing for each relevant Value chain:
            for Index = 1:numel(testCase.list_of_valuechains)
                % Drop_down_entry = testCase.ValueChains{testCase.list_of_valuechains(Index)}; % indes is only number of entry (which then gives the number of value chain)
                % disp(Drop_down_entry)
                testCase.choose(testCase.MainApp.DropDown_ChooseWSK, testCase.ValueChains{testCase.list_of_valuechains(Index)});
                % open and Close the Window
                open_close_KPI_Window(testCase, testCase.Window_Name, testCase.MainApp.Button_Electrolyzer);
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
                % open the Window
                testCase.press(testCase.MainApp.Button_Electrolyzer);
                %%  set power rating to zero
                testCase.type(testCase.MainApp.KPIWindow.NennleistungEditField, 0)
                testCase.press(testCase.MainApp.KPIWindow.OKButton);
                testCase.assertEqual(testCase.MainApp.KPIWindowOpen,0);
                
                %Berechnung starten
                testCase.press(testCase.MainApp.BerechnungStartenButton);
                %Ergebnisse anzeigen:
                testCase.press(testCase.MainApp.ResultsButton);
                testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
                testCase.assertEqual(class(testCase.MainApp.ResultsWindow),'ResultsGUI_SingleRun')
                
                % no Power installed
                testCase.assertEqual(testCase.MainApp.ResultsWindow.NennleistungEditField_Ely.Value, 0)
                % no Full load hours
                testCase.assertEqual(testCase.MainApp.ResultsWindow.VolllaststundenEditField_Ely.Value, 0)
                % --> results should show no produced Hydrogen
                testCase.assertEqual(testCase.MainApp.ResultsWindow.H2ProducedkWhEditField.Value, 0)
                % --> no Cost 
                testCase.assertEqual(testCase.MainApp.ResultsWindow.InvestitionskostenEditField_Ely.Value, 0)
                % --> no Cost 
                testCase.assertEqual(testCase.MainApp.ResultsWindow.BetriebskostenEditField_Ely.Value, 0)

            end
            testCase.MainApp.TearDown;
        end
        function switch_technology(testCase)
                    % set up Main GUI
                    testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
                    % test opening and closing for each relevant Value chain:
                    for Index = 1:numel(testCase.list_of_valuechains)
                        Drop_down_entry = testCase.ValueChains{testCase.list_of_valuechains(Index)}; % indes is only number of entry (which then gives the number of value chain)
                        testCase.choose(testCase.MainApp.DropDown_ChooseWSK, Drop_down_entry);
                        testCase.press(testCase.MainApp.Button_Electrolyzer);

                        for technology_index = 1:numel(testCase.MainApp.KPIWindow.TechnologieDropDown.Items)

                            %% testin calc for all technology options
                            tech_string = testCase.MainApp.KPIWindow.TechnologieDropDown.Items{technology_index};
                            disp(['testing', tech_string])
                            testCase.choose(testCase.MainApp.KPIWindow.TechnologieDropDown, tech_string);

                            testCase.press(testCase.MainApp.KPIWindow.OKButton);
                            testCase.assertEqual(testCase.MainApp.KPIWindowOpen,0);
                            %Berechnung starten
                            testCase.press(testCase.MainApp.BerechnungStartenButton);
                            %Ergebnisse anzeigen:
                            testCase.press(testCase.MainApp.ResultsButton);
                            testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1);
                            testCase.press(testCase.MainApp.Button_Electrolyzer);
                        end
                    end
        end
        
    end
end


