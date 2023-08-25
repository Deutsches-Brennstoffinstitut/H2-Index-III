close all;
clc;
clear;

addpath(genpath('tests'));

% INI results structure:
Results = matlab.unittest.TestResult;
% what Tests to do:
ListOfTestFiles = {'test_ResultsGUI_SingleRun.m', ...
                    'test_KPIWindow_EE_Source.m', ...
                    'test_KPIWindow_Consumer.m', ...
                    'test_KPIWindow_Grid.m', ...
					'test_KPIWindow_Ely.m', ...
					'test_KPIWindow_Storage.m', ...
					'test_KPIWindow_Transport.m'
                   };

for ThisTestFileIndex = 1: numel(ListOfTestFiles)
    %disp(ListOfTestFiles{ThisTestFileIndex})
    try
        TMP_Results = runtests(ListOfTestFiles{ThisTestFileIndex});
        Results = cat(2,Results,TMP_Results);
    catch
        errordlg(strcat('Fatal error in ' + string(ListOfTestFiles{ThisTestFileIndex})))
    end
end
 
%% output results here:
fprintf('Failed Tests:\n')
NumberOfFailedtests = 0;
for TestIndex =1:numel(Results)
    if Results(TestIndex).Failed
        NumberOfFailedtests = NumberOfFailedtests + 1;
        fprintf('%s\n',Results(TestIndex).Name)
    end
end
if NumberOfFailedtests == 0
    fprintf('NONE:\n')
end