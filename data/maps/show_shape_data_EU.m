clear;
clc;
load('Europe_clean.mat')

%% show Nuts3 Regions:
ThisFigure = figure;
for RegionIndex = 1: numel(Europe_clean)
    plot(Europe_clean(RegionIndex).X',Europe_clean(RegionIndex).Y','Color',[51 101 138 125]/255,'LineWidth',1);
    hold on 
end
hold off
axis off 
grid off
title('NUTS 3 Regions')
% rescale axis:
%Calculate the distances along the axis
Thisaxes = gca;
x_dist = (Thisaxes.XLim(1) - Thisaxes.XLim(2));
y_dist = (Thisaxes.YLim(1) - Thisaxes.YLim(2));
%Adjust the aspect ratio
c_adj = cosd(mean(Thisaxes.YLim(1:2)))*1.2;
dar = [1 c_adj 1];
pbar = [x_dist*c_adj/y_dist 1 1];
set(Thisaxes, 'DataAspectRatio',dar,'PlotBoxAspectRatio',pbar);

set(ThisFigure, 'renderer','opengl',...
    'InvertHardcopy', 'on',...
    'DefaultAxesFontSize', 11, ...
    'DefaultAxesFontName','Arial',...
    'PaperOrientation', 'portrait',...
    'PaperUnits', 'normalized',...
    'Papertype', 'a4',...% only relevant for png prints
    'PaperPositionMode', 'manual',...
    'PaperPosition', [0 0 1 1]);
%align_axislabel([], TheseAxis)
%print('Grafiken\NUTS3_DE','-dmeta');
%print('Grafiken\NUTS3_DE','-djpeg');


