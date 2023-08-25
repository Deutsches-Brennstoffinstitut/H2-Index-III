function [testCase, CurrentProfile]  = test_NeuesProfileinlesenButtonPushed(testCase, FileName)
    % the following code simulates:
    % testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.NeuesProfileinlesenButtonPushed();   % Call the button callback function
    
    % Simulate file selection
    [CurrentProfile, ~,error_ID] = read_profile(FileName);
    testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.CurrentProfile = CurrentProfile;
    if error_ID == 0
        % Update GUI based on the selected file
        if max(CurrentProfile) ~= 0
            testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.BasisNennleistung = round(max(testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.CurrentProfile));
            testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.CurrentProfile_norm = testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.CurrentProfile/ testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.BasisNennleistung;
        else
            testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.CurrentProfile_norm = testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.CurrentProfile;
            testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.BasisNennleistung = 0;
        end
    
        testCase.MainApp.KPIWindow.QuellenBearbeitenWindow.UpDateProfilLadenWindow(); % Update the profile loading window
    end
end