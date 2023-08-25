clear
clc
%% Starting script for the H2-Index III Tool
try
    pe = pyenv('Version',"venv\Scripts\python.exe");
catch
    disp('python environment not found or already activated')
end
% Start Script f�r kompiliertes Project:
if ~isdeployed % nicht die kompilierte/ installierte Version, sondern l�uft direkt aus Matlab
    % zus�tzlicher Suchpfad:
    addpath(genpath('base_python'));
    addpath(genpath('base_matlab'));
    addpath(genpath('data'));
end

if exist('MainData','var')== 1
    disp('Programm l�uft bereits');
    MainData.delete();
    MainData = MainGUI();
else
    MainData = MainGUI();
end