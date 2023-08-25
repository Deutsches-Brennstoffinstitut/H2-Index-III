classdef test_ResultsGUI_SingleRun < matlab.uitest.TestCase% subclass of matlab.uitest.TestCase
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
            testCase.ValueChains = testCase.MainApp.DropDown_ChooseWSK.Items; % all entries in the dropdown menue
            testCase.addTeardown(@delete,testCase.MainApp);
            testCase.addTeardown(@delete,testCase.MainApp.ResultsWindow);
            import matlab.unittest.constraints.IsGreaterThan
            import matlab.unittest.constraints.IsEqualTo
        end
    end
    
    methods (Test)
        
        function Single_ValueChain_Result_Window(testCase)
            % import matlab.unittest.constraints.IsEqualTo
            % import matlab.unittest.constraints.IsGreaterThan
            
            % set up Main GUI
            testCase.choose(testCase.MainApp.ObjectiveDropDown,'Single Value Chain');
            % test opening and closing for each relevant Value chain:
            for Drop_down_entry = testCase.ValueChains
                disp(Drop_down_entry)
                testCase.choose(testCase.MainApp.DropDown_ChooseWSK, Drop_down_entry);
                SubtestForResultWindow(testCase)
            end
            testCase.MainApp.TearDown;
     
        end
        
        
    end
end


