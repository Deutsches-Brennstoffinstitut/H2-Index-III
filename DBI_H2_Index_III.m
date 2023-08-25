clear
clc
%% Starting script for the H2-Index III Tool
try
    pe = pyenv('Version',"venv\Scripts\python.exe");
catch
    disp('python environment not found or already activated')
end
% Start Script für kompiliertes Project:
if ~isdeployed % nicht die kompilierte/ installierte Version, sondern läuft direkt aus Matlab
    % zusätzlicher Suchpfad:
    addpath(genpath('base_python'));
    addpath(genpath('base_matlab'));
    addpath(genpath('data'));
end

if exist('MainData','var')== 1
    disp('Programm läuft bereits');
    MainData.delete();
    MainData = MainGUI();
else
    MainData = MainGUI();
end