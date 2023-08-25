
function open_close_KPI_Window(testCase, Window_Name, Button_Name)
    testCase.press(Button_Name);
    testCase.assertEqual(class(testCase.MainApp.KPIWindow), Window_Name)
    testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
    testCase.press(testCase.MainApp.KPIWindow.OKButton);
    testCase.assertEqual(testCase.MainApp.KPIWindowOpen,0)

    testCase.press(Button_Name);

    testCase.assertEqual(class(testCase.MainApp.KPIWindow),Window_Name)
    testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
    testCase.press(testCase.MainApp.KPIWindow.CancelButton);
    testCase.assertEqual(testCase.MainApp.KPIWindowOpen,0)
    % close window by pressing x + eingabe abbrechen

    testCase.press(Button_Name);

    testCase.assertEqual(class(testCase.MainApp.KPIWindow),Window_Name)
    testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
    testCase.MainApp.KPIWindow.WhileTesting = true;
    testCase.MainApp.KPIWindow.Abbruchentscheidung = 'No';
    testCase.MainApp.KPIWindow.TearDown;
    testCase.assertEqual(testCase.MainApp.KPIWindowOpen,0)
    % close window by pressing x + eingabe übernehmen

    testCase.press(Button_Name);

    testCase.assertEqual(class(testCase.MainApp.KPIWindow),Window_Name)
    testCase.assertEqual(testCase.MainApp.KPIWindowOpen,1)
    testCase.MainApp.KPIWindow.WhileTesting = true;
    testCase.MainApp.KPIWindow.Abbruchentscheidung = 'Yes';
    testCase.MainApp.KPIWindow.TearDown;
    testCase.assertEqual(testCase.MainApp.KPIWindowOpen,0)

end