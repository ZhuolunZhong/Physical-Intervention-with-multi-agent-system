import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';

const SurveyPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { state } = location;
  const message = state?.message || 'Default Survey Message';

  const [response, setResponse] = useState('');

  const uploadSurveyResponseToServer = async () => {
    const user_id = sessionStorage.getItem('userID') || 'unknown';
    const round = parseInt(sessionStorage.getItem('round') || '1', 10);

    const surveyData = {
      user_id,
      round,
      response
    };

    try {
      const response = await axios.post('/api/upload/mysql4', {
        data: surveyData
      });
      console.log("Survey response uploaded:", response.data);
    } catch (error) {
      console.error("Error uploading survey response:", error);
      throw error; 
    }
  };

  const handleSubmit = async () => {
    if (!response.trim() && message !== 'You will train one agent in the next two rounds. ') {
      alert('Please fill in your response before submitting.');
      return;
    }

    try {
      if (message !== 'You will train one agent in the next two rounds. ') {
        await uploadSurveyResponseToServer();
      }

      if (message === 'Please complete the final survey carefully and make sure to note the special code you receive after submission.') {
        window.location.href = '/finished';
      } else {
        window.location.href = '/main_expt';
      }
    } catch (error) {
      console.error('Survey response upload failed, aborting navigation.');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      {message !== 'You will train one agent in the next two rounds. ' && (
        <div style={{ marginBottom: '20px' }}>
          <h2>1、Please briefly describe your teaching strategy and explain why you chose this strategy for the last 2 rounds.</h2>
          <textarea
            value={response}
            onChange={(e) => setResponse(e.target.value)}
            rows={5}
            style={{ width: '100%', padding: '10px', fontSize: '16px' }}
          />
        </div>
      )}

      <div style={{ marginBottom: '20px' }}>
        <h2>{message !== 'You will train one agent in the next two rounds. ' ? `2、${message}` : message}</h2>
      </div>

      <button
        onClick={handleSubmit}
        style={{
          padding: '10px 20px',
          fontSize: '16px',
          cursor: 'pointer',
          backgroundColor: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '4px'
        }}
      >
        Press to Continue
      </button>
    </div>
  );
};

export default SurveyPage;
