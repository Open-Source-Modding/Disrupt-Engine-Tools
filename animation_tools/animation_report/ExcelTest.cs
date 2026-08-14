using System;
using System.Collections.Generic;
using Excel = Microsoft.Office.Interop.Excel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace AnimationReport
{
    class ExcelTest
    {
        public static void Test()
        {
            //Get a reference to Excel and check to ensure its installed
            Excel.Application xlApp = new Microsoft.Office.Interop.Excel.Application();
            if (xlApp == null)
            {
                Console.WriteLine("Excel is not properly installed!!");
                return;
            }

            Console.WriteLine("Generating your report. Patience, please....");
            xlApp.ScreenUpdating = false;

            //Create a new Excel Workbool file
            object misValue = System.Reflection.Missing.Value;
            Excel.Workbook workbook = xlApp.Workbooks.Add(misValue);

            //Create the headers
            Excel.Worksheet sheetCLOs = (Excel.Worksheet)workbook.Worksheets.get_Item(1);
            string[] headerNames = { "CLO Name", "whatever", "whatever", "whatever", "whatever", "whatever", "more whatever"};
            int[,] myInt = new int[2500, 8];
            Excel.Range headerRange = sheetCLOs.get_Range((object)sheetCLOs.Cells[1, 1], (object)sheetCLOs.Cells[1, headerNames.Length]);
            headerRange.Value = headerNames;
            headerRange.Cells.Font.Bold = true;
            headerRange.Cells.Interior.Color = Excel.XlRgbColor.rgbLightSteelBlue;

            //Excel.Range dataRange = sheetCLOs.get_Range((object)sheetCLOs.Cells[2, 1], (object)sheetCLOs.Cells[2, myInt.Length]);

            Console.WriteLine(myInt.GetLength(0));
            Excel.Range dataRange = sheetCLOs.get_Range((object)sheetCLOs.Cells[2, 1], (object)sheetCLOs.Cells[myInt.GetLength(0), myInt.GetLength(1)]);
            dataRange.Value = myInt;

            var lastRow = sheetCLOs.UsedRange.Rows.Count;
            Excel.Range testRange = sheetCLOs.get_Range("B2", $"B{lastRow}");
            testRange.Cells.Font.Bold = true;
            Excel.Range rngHeader = sheetCLOs.get_Range("A1", "F1");
            rngHeader.AutoFilter(1);

            sheetCLOs.Application.ActiveWindow.SplitRow = 1;
            sheetCLOs.Application.ActiveWindow.FreezePanes = true;

            //for (int i = 2; i < myInt.GetLength(0); i++)
            //{
            //    Excel.Range dataRange = sheetCLOs.get_Range((object)sheetCLOs.Cells[i, 1], (object)sheetCLOs.Cells[i, myInt.GetLength(0)]);
            //    dataRange.Value = myInt;
            //}


            //Save the file and close the Excel application processes
            xlApp.ScreenUpdating = true;
            xlApp.DisplayAlerts = false;
            workbook.SaveAs(@"C:\Users\sdiehl\Documents\Scripts\OutputFiles\Test.xls", Excel.XlFileFormat.xlWorkbookNormal);
            workbook.Close(true, misValue, misValue);
            xlApp.Workbooks.Open(@"C:\Users\sdiehl\Documents\Scripts\OutputFiles\Test.xls");
            xlApp.DisplayAlerts = true;
            xlApp.Visible = true;
            //xlApp.Quit();
        }
    }
}
