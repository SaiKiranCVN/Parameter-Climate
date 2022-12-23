import "./App.css";
import React, { useState } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";

function App() {
  // Declare state variables to store the user input
  const [startDate, setStartDate] = useState(new Date());
  const [endDate, setEndDate] = useState(new Date());
  const [months, setMonths] = useState(0);
  const [powerPriceStrike, setPowerPriceStrike] = useState(300);
  const [mwNotional, setMwNotional] = useState(100);
  const [futuresLevel, setFuturesLevel] = useState(179);
  const [strikeCallPrice, setStrikeCallPrice] = useState(87.0);
  const [isLoading, setIsLoading] = useState(true);
  const [formVisible, setFormVisible] = useState(true);

  // Declare a function to handle the form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    // Make an HTTP request to the Flask endpoint using the fetch function
    const response = await fetch("http://127.0.0.1:5000/process", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
      body: JSON.stringify({
        startDate,
        endDate,
        monthlyData,
        powerPriceStrike,
        mwNotional,
        futuresLevel,
        strikeCallPrice,
      }),
    });
    // Process the response from the Flask endpoint and display the output
  };
  const [monthlyData, setMonthlyData] = useState([]);

  function handleInputChange(event, index) {
    const newMonthlyData = [...monthlyData];
    newMonthlyData[index] = event.target.value;
    setMonthlyData(newMonthlyData);
  }

  return (
    <>
      {formVisible && (
        <form className='form' onSubmit={handleSubmit}>
          <div className='form-group'>
            <label htmlFor='startDate'>From Date:</label>
            <DatePicker
              id='startDate'
              selected={startDate}
              onChange={(date) => setStartDate(date)}
              className='form-control'
            />
          </div>
          <div className='form-group'>
            <label htmlFor='endDate'>To Date:</label>
            <DatePicker
              id='endDate'
              selected={endDate}
              onChange={(date) => {
                setEndDate(date);
                setMonths(monthsBetween(startDate, endDate));
              }}
              className='form-control'
            />
          </div>
          {Array.from(Array(months)).map((_, index) => (
            <div key={index} className='form-group'>
              <label>TMAX Month {index + 1}:</label> <br />
              <input
                type='text'
                value={monthlyData[index] || ""}
                className='form-control'
                onChange={(event) => handleInputChange(event, index)}
              />
            </div>
          ))}
          <div className='form-group'>
            <label htmlFor='powerPriceStrike'>Power Price Strike:</label>
            <input
              type='number'
              id='powerPriceStrike'
              value={powerPriceStrike}
              onChange={(e) => setPowerPriceStrike(e.target.value)}
              className='form-control'
            />
          </div>
          <div className='form-group'>
            <label htmlFor='mwNotional'>MW Notional:</label>
            <input
              type='number'
              id='mwNotional'
              value={mwNotional}
              onChange={(e) => setMwNotional(e.target.value)}
              className='form-control'
            />
          </div>
          <div className='form-group'>
            <label htmlFor='futuresLevel'>Futures Level:</label>
            <input
              type='number'
              id='futuresLevel'
              value={futuresLevel}
              onChange={(e) => setFuturesLevel(e.target.value)}
              className='form-control'
            />
          </div>
          <div className='form-group'>
            <label htmlFor='strikeCallPrice'>300 Strike Call Price:</label>
            <input
              type='number'
              id='strikeCallPrice'
              value={strikeCallPrice}
              onChange={(e) => setStrikeCallPrice(e.target.value)}
              className='form-control'
            />
          </div>
          <button type='submit' className='btn btn-primary'>
            Submit
          </button>
        </form>
      )}
    </>
  );
}

function monthsBetween(startDate, endDate) {
  // Create date objects
  const start = new Date(startDate);
  const end = new Date(endDate);

  // Calculate the difference in milliseconds
  const difference = end.getTime() - start.getTime();

  if (difference <= 0) {
    alert("The end date must be after the start date!");
    return;
  }

  // Convert the difference to months
  const months = Math.floor(difference / (30.44 * 24 * 60 * 60 * 1000));
  // setMonths(months);
  console.log(start, end, months);
  return months
    ? months
    : 1; /* Case where we have less than one moth difference */
}

export default App;
