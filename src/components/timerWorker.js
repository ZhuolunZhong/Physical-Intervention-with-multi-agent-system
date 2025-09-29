let currentTime = 0;
let interval = null;

// The additional components required for the timer to function properly 
onmessage = function(event) {
  if (event.data === 'start') {
    interval = setInterval(() => {
      currentTime += 100; 
      if (currentTime % 500 === 0) { 
        postMessage(currentTime / 1000); 
      }
    }, 100); 
  } else if (event.data === 'stop') {
    clearInterval(interval);
  }
};
