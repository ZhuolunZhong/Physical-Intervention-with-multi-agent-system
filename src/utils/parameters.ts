import axios from 'axios';

// Define an interface for the parameters object
interface Parameters {
  NUM_AGENTS: number;
  PELLET_PATCH_MEAN2: number[][];
  PELLET_PATCH_VAR2: number[][];
  EXPECTED_PELLET_TIME: number;
  AGENT_EPS: number;
  TEACH_EPS: number;
  MOVE_TIME: number;
  WAIT_TIME: number;
  Q_STEP_COST: number;
  HUM_INT_FB: number;
  PELLET_FEEDBACK: number;
  INTERPRET_TYPE: number;
  agentTypes: string[];
  PELLET_TILES: number[][];
}

// Function to fetch parameters from the server based on the round number
export async function fetchParameters(round: number): Promise<Parameters | null> {
  try {
    // Make a GET request to the server to fetch parameters
    const response = await axios.get(`/api/parameters?round=${round}`);
    return response.data; // Return the fetched parameters
  } catch (error: unknown) {
    // Handle errors
    if (axios.isAxiosError(error)) {
      if (error.response && error.response.status === 404) {
        return null; // Return null if the resource is not found
      }
      console.error('Axios error fetching parameters:', error.message); // Log Axios errors
    } else {
      console.error('Unknown error fetching parameters:', error); // Log unknown errors
    }
    return null; // Return null in case of any error
  }
}

// Function to initialize parameters by fetching and storing them in sessionStorage
export async function initializeParameters(): Promise<void> {
  // Get the current round number from sessionStorage
  let round = sessionStorage.getItem('round');
  if (!round) {
    // If no round is set, default to round 1
    round = '1';
    sessionStorage.setItem('round', round);
  }

  // Fetch parameters for the current round
  const parameters = await fetchParameters(parseInt(round, 10));
  if (parameters) {
    // Store each parameter in sessionStorage
    Object.keys(parameters).forEach((key) => {
      sessionStorage.setItem(key, JSON.stringify(parameters[key as keyof Parameters]));
    });
    // If the simulation is not yet initialized, reload the page
    if (!sessionStorage.getItem('initialized')) {
      sessionStorage.setItem('initialized', 'true');
      window.location.reload();  
    }
  }
}

// Function to increment the round number and update it in sessionStorage
export function incrementRound(): number {
  // Get the current round number from sessionStorage
  let round = parseInt(sessionStorage.getItem('round') || '1', 10);
  round += 1; // Increment the round number
  sessionStorage.setItem('round', round.toString()); // Update the round in sessionStorage
  return round; // Return the new round number
}

// Function to update parameters by fetching them for the current round
export async function updateParameters(): Promise<void> {
  // Get the current round number from sessionStorage
  const round = sessionStorage.getItem('round');
  if (round) {
    // Fetch parameters for the current round
    const parameters = await fetchParameters(parseInt(round, 10));
    if (parameters) {
      // Update each parameter in sessionStorage
      Object.keys(parameters).forEach((key) => {
        sessionStorage.setItem(key, JSON.stringify(parameters[key as keyof Parameters]));
      });
    }
  }
}

// Function to retrieve a parameter from sessionStorage with a default value
export function getSessionStorageParam<T>(key: string, defaultValue: T): T {
  // Get the stored value from sessionStorage
  const storedValue = sessionStorage.getItem(key);
  if (storedValue !== null) {
    return JSON.parse(storedValue) as T; // Return the parsed value
  }
  return defaultValue; // Return the default value if no value is stored
}

// Function to handle the completion of a round
export async function onRoundComplete(): Promise<void> {
  incrementRound(); // Increment the round number
  await updateParameters(); // Update parameters for the new round
}