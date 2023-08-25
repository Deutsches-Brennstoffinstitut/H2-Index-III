function SubtestForResultWindow(testCase)
import matlab.unittest.constraints.IsGreaterThan
import matlab.unittest.constraints.IsEqualTo

testCase.press(testCase.MainApp.BerechnungStartenButton);
%% assert results of some kind here:
testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,0)% closes with pressing "Berechnung Starten"
testCase.press(testCase.MainApp.ResultsButton);
testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,1)

%testCase.assertNotEqual(testCase.MainApp.ResultsWindow.InvestitionGesamtEditField.Value,NaN)
AllGUIFields = fieldnames(testCase.MainApp.ResultsWindow);
for ThisNamesIndex = 1:numel(AllGUIFields)
    ThisName = AllGUIFields{ThisNamesIndex};
    % Eingabefelder Sinnvoll gefüllt?
    if isa(testCase.MainApp.ResultsWindow.(ThisName),'matlab.ui.control.NumericEditField')
        testCase.assertNotEqual(testCase.MainApp.ResultsWindow.(ThisName).Value, NaN)
        testCase.verifyThat(testCase.MainApp.ResultsWindow.(ThisName).Value, IsGreaterThan(0) | IsEqualTo(0))
    end
    %Grafiken gefüllt?
    if isa(testCase.MainApp.ResultsWindow.(ThisName),'matlab.ui.control.UIAxes')
        ThisAxisObject = testCase.MainApp.ResultsWindow.(ThisName);
        dataObjs = ThisAxisObject.Children;
        testCase.assertNotEmpty(dataObjs);
    end
end

% close window
testCase.MainApp.ResultsWindow.TearDown;
testCase.assertEqual(testCase.MainApp.ResultsWindowOpen,0)
end