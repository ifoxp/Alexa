using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace AlexaS
{
    internal static class Program
    {
        private static Mutex mutex = null;

        /// <summary>
        /// The main entry point for the application.
        /// </summary>
        [STAThread]
        static void Main()
        {
            // Захист від подвійного запуску
            const string mutexName = "AlexaSettingsAppMutex";
            bool createdNew;

            mutex = new Mutex(true, mutexName, out createdNew);

            if (!createdNew)
            {
                // Якщо програма вже запущена, покажемо повідомлення і активуємо існуюче вікно
                MessageBox.Show("Налаштування Alexa вже відкрито!", "Увага",
                               MessageBoxButtons.OK, MessageBoxIcon.Information);

                // Спробуємо знайти та активувати існуюче вікно
                ActivateExistingWindow();
                return;
            }

            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            try
            {
                Application.Run(new Form1());
            }
            finally
            {
                if (mutex != null)
                {
                    mutex.ReleaseMutex();
                    mutex.Dispose();
                }
            }
        }

        private static void ActivateExistingWindow()
        {
            try
            {
                Process currentProcess = Process.GetCurrentProcess();
                Process[] processes = Process.GetProcessesByName(currentProcess.ProcessName);

                foreach (Process process in processes)
                {
                    if (process.Id != currentProcess.Id && !string.IsNullOrEmpty(process.MainWindowTitle))
                    {
                        // Активуємо знайдене вікно
                        ShowWindow(process.MainWindowHandle, SW_RESTORE);
                        SetForegroundWindow(process.MainWindowHandle);
                        break;
                    }
                }
            }
            catch (Exception)
            {
                // Ігноруємо помилки при активації вікна
            }
        }

        [System.Runtime.InteropServices.DllImport("user32.dll")]
        private static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

        [System.Runtime.InteropServices.DllImport("user32.dll")]
        private static extern bool SetForegroundWindow(IntPtr hWnd);

        private const int SW_RESTORE = 9;
    }
}
