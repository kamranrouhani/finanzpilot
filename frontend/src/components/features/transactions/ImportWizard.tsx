/**
 * Import wizard for Finanzguru XLSX/CSV files.
 */
'use client';

import { useState } from 'react';
import { importTransactions, type TransactionImportResponse } from '@/lib/api/transactions';

interface ImportWizardProps {
  token: string;
  onImportComplete?: (result: TransactionImportResponse) => void;
}

export function ImportWizard({ token, onImportComplete }: ImportWizardProps) {
  const [file, setFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<TransactionImportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
      setResult(null);
    }
  };

  const handleImport = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setImporting(true);
    setError(null);

    try {
      const importResult = await importTransactions(token, file, true);
      setResult(importResult);
      onImportComplete?.(importResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed');
    } finally {
      setImporting(false);
    }
  };

  const reset = () => {
    setFile(null);
    setResult(null);
    setError(null);
  };

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold mb-4">Import Transactions</h2>
        <p className="text-gray-600 mb-6">
          Upload a Finanzguru XLSX or CSV export file to import your transactions.
        </p>

        {!result ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select File
              </label>
              <input
                type="file"
                accept=".xlsx,.csv"
                onChange={handleFileChange}
                className="block w-full text-sm text-gray-500
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-md file:border-0
                  file:text-sm file:font-semibold
                  file:bg-blue-50 file:text-blue-700
                  hover:file:bg-blue-100
                  cursor-pointer"
                disabled={importing}
              />
              {file && (
                <p className="mt-2 text-sm text-gray-600">
                  Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
                </p>
              )}
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={handleImport}
                disabled={!file || importing}
                className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                {importing ? 'Importing...' : 'Import'}
              </button>
              {file && !importing && (
                <button
                  onClick={reset}
                  className="bg-gray-200 text-gray-700 px-6 py-2 rounded-md hover:bg-gray-300"
                >
                  Cancel
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-green-900 mb-4">
                Import Complete!
              </h3>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">Total Rows</p>
                  <p className="text-2xl font-bold text-gray-900">{result.total_rows}</p>
                </div>
                <div>
                  <p className="text-gray-600">Imported</p>
                  <p className="text-2xl font-bold text-green-600">{result.imported}</p>
                </div>
                <div>
                  <p className="text-gray-600">Skipped (Duplicates)</p>
                  <p className="text-2xl font-bold text-yellow-600">{result.skipped}</p>
                </div>
                <div>
                  <p className="text-gray-600">Errors</p>
                  <p className="text-2xl font-bold text-red-600">{result.errors}</p>
                </div>
              </div>

              {result.error_details && result.error_details.length > 0 && (
                <div className="mt-4">
                  <p className="text-sm font-medium text-red-700 mb-2">Error Details:</p>
                  <ul className="text-sm text-red-600 space-y-1">
                    {result.error_details.map((error, idx) => (
                      <li key={idx}>• {error}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <button
              onClick={reset}
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700"
            >
              Import Another File
            </button>
          </div>
        )}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">Instructions</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Export your transactions from Finanzguru app</li>
          <li>• Supported formats: XLSX, CSV</li>
          <li>• Duplicate transactions will be automatically skipped</li>
          <li>• All Finanzguru metadata will be preserved</li>
        </ul>
      </div>
    </div>
  );
}
