import React, { useEffect } from 'react';
import { useSelector } from "react-redux";
import { agentInsts } from './Grid';
import { useNumTrajData } from "./DataLog";

// Function to convert expected q value data to CSV format

// @ts-ignore
const convertToCSV = (array) => {
  let csvContent = "data:text/csv;charset=utf-8,"; // Initialize CSV content with header
  csvContent += "agentid,ExpectedQvalue\n"; // Add CSV column headers
  // @ts-ignore
  array.forEach(item => {
    csvContent += `${item.agentid},${item.ExpectedQvalue}\n`; // Add each row of data
  });

  return csvContent; // Return the complete CSV content
};

// Function to download an object as a JSON file
// @ts-ignore
function downloadObjectAsJson(exportObj, exportName){
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(exportObj)); // Convert object to JSON string
  const downloadAnchorNode = document.createElement('a'); // Create a temporary anchor element
  downloadAnchorNode.setAttribute("href", dataStr); // Set the href attribute to the JSON data
  downloadAnchorNode.setAttribute("download", exportName + ".json"); // Set the download attribute with the file name
  document.body.appendChild(downloadAnchorNode); // Append the anchor to the document
  downloadAnchorNode.click(); // Trigger the download
  downloadAnchorNode.remove(); // Remove the anchor from the document
}

// Function to download a CSV file
// @ts-ignore
function downloadCSV(csvContent, fileName) {
  const encodedUri = encodeURI(csvContent); // Encode the CSV content as a URI
  const link = document.createElement("a"); // Create a temporary anchor element
  link.setAttribute("href", encodedUri); // Set the href attribute to the CSV data
  link.setAttribute("download", fileName + ".csv"); // Set the download attribute with the file name
  document.body.appendChild(link); // Append the anchor to the document
  link.click(); // Trigger the download
  document.body.removeChild(link); // Remove the anchor from the document
}

// Define the ExportButton component
const ExportButton = () => {
  // @ts-ignore
  const qData = useSelector((state) => state.extradata.qResults); // Access Q-results data from the Redux store
  // @ts-ignore
  const QTable = (agentInsts[0])._myQTable; // Access the Q-table policy of the first agent
  // @ts-ignore
  const numMoves0 = useNumTrajData(0); // Get the number of moves using the custom hook
  // @ts-ignore
  const numMoves1 = useNumTrajData(1); // Get the number of moves using the custom hook

  const hasDownloaded = React.useRef(false);
  
  // useEffect hook to trigger the download and reload the page when the number of moves reaches 600
  useEffect(() => {
    const minMoves = Math.min(numMoves0, numMoves1);
    if (minMoves === 1001 && !hasDownloaded.current) {
      hasDownloaded.current = true;
      handleDownload();
      window.location.reload();
    }
  }, [numMoves0, numMoves1]);

  // Function to handle the download process
  const handleDownload = () => {
    //const fileName = generateFileName(); // Generate the file name
    const csvContent = convertToCSV(qData); // Convert Q-results data to CSV
    //downloadObjectAsJson(QTable, fileName); // Download the Q-table policy as a JSON file
    downloadCSV(csvContent, 'exportedData'); // Download the CSV file
  };

  // Render the component UI
  return <button onClick={handleDownload}>Download CSV</button>; // Render a button to trigger the download
};

export default ExportButton; 