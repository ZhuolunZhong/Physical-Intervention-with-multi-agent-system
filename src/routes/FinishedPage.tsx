import React, { useState } from 'react';
import axios from 'axios';

const FinishedPage = () => {
  const [hasRobotVacuum, setHasRobotVacuum] = useState<boolean | null>(null);
  const [satisfaction, setSatisfaction] = useState(4);
  const [showDialog, setShowDialog] = useState(false);
  const [gender, setGender] = useState('');
  const [race, setRace] = useState('');
  const [age, setAge] = useState<number | ''>('');
  const [understandsScoring, setUnderstandsScoring] = useState<boolean | null>(null); // 新增状态

  const handleSubmit = async () => {
    const user_id = sessionStorage.getItem('userID') || 'unknown';

    if (hasRobotVacuum === null) {
      alert("Please select whether you have a robotic vacuum.");
      return;
    }
    if (!gender) {
      alert("Please select your gender.");
      return;
    }
    if (!race) {
      alert("Please select your race.");
      return;
    }
    if (age === '' || age <= 0) {
      alert("Please enter a valid age.");
      return;
    }
    if (understandsScoring === null) {
      alert("Please confirm your understanding of the scoring rule.");
      return;
    }

    const surveyData = {
      user_id,
      hasRobotVacuum,
      satisfaction: hasRobotVacuum ? satisfaction : 0,
      gender,
      race,
      age,
      understands_scoring: understandsScoring, 
    };

    try {
      const response = await axios.post('/api/upload/mysql5', { data: surveyData });
      console.log("Survey response uploaded:", response.data);
      setShowDialog(true);
    } catch (error) {
      console.error("Error uploading survey response:", error);
      alert("There was an error submitting your response. Please try again.");
    }
  };

  return (
    <div>
      <h1>Survey</h1>

      {/* Question 1 */}
      <div>
        <p>Do you have a robotic vacuum at home?</p>
        <label>
          <input
            type="radio"
            name="robotVacuum"
            value="yes"
            checked={hasRobotVacuum === true}
            onChange={() => setHasRobotVacuum(true)}
          />
          Yes
        </label>
        <label>
          <input
            type="radio"
            name="robotVacuum"
            value="no"
            checked={hasRobotVacuum === false}
            onChange={() => setHasRobotVacuum(false)}
          />
          No
        </label>
      </div>

      {/* Question 2 (conditional) */}
      {hasRobotVacuum && (
        <div>
          <p>How satisfied are you with it? (1 = Not satisfied, 7 = Very satisfied)</p>
          <input
            type="range"
            min="1"
            max="7"
            value={satisfaction}
            onChange={(e) => setSatisfaction(parseInt(e.target.value, 10))}
          />
          <div style={{ marginTop: '10px', textAlign: 'left' }}>Value: {satisfaction}</div>
        </div>
      )}

      {/* Gender Selection */}
      <div>
        <p>What is your gender?</p>
        <select value={gender} onChange={(e) => setGender(e.target.value)}>
          <option value="">Select</option>
          <option value="male">Male</option>
          <option value="female">Female</option>
          <option value="other">Other</option>
          <option value="prefer_not_to_say">Prefer not to say</option>
        </select>
      </div>

      {/* Race Selection */}
      <div>
        <p>What is your race?</p>
        <select value={race} onChange={(e) => setRace(e.target.value)}>
          <option value="">Select</option>
          <option value="asian">Asian</option>
          <option value="black">Black or African American</option>
          <option value="white">White</option>
          <option value="hispanic">Hispanic or Latino</option>
          <option value="other">Other</option>
          <option value="prefer_not_to_say">Prefer not to say</option>
        </select>
      </div>

      {/* Age Input */}
      <div>
        <p>What is your age?</p>
        <input
          type="number"
          value={age}
          onChange={(e) => setAge(e.target.value ? parseInt(e.target.value, 10) : '')}
          placeholder="Enter your age"
        />
      </div>

      {/* Understand rule */}
      <div>
        <p>During the experiment you just completed, did you understand the following rule?</p>
        <div style={{ 
          backgroundColor: '#f5f5f5', 
          padding: '15px', 
          margin: '10px 0',
          borderRadius: '5px',
          border: '1px solid #ddd'
        }}>
          <strong>Note:</strong> Points collected by the agent immediately when you drop the agent do not count towards the agent's score and its learning. To get a point, the agent must move there by its own volition.
        </div>
        <p>Did you understand this scoring rule during the experiment?</p>
        <label>
          <input
            type="radio"
            name="scoringRule"
            value="yes"
            checked={understandsScoring === true}
            onChange={() => setUnderstandsScoring(true)}
          />
          Yes, I understood this rule during the experiment
        </label>
        <label>
          <input
            type="radio"
            name="scoringRule"
            value="no"
            checked={understandsScoring === false}
            onChange={() => setUnderstandsScoring(false)}
          />
          No, I did not understand this rule during the experiment
        </label>
      </div>

      {/* Submit Button */}
      <button onClick={handleSubmit}>Submit</button>

      {/* Custom Dialog */}
      {showDialog && (
        <div className="confirm-dialog-overlay">
          <div className="confirm-dialog">
            <h2>Thank you for your participation. Use CODE 511493 to complete your work.</h2>
          </div>
        </div>
      )}
    </div>
  );
};

export default FinishedPage;