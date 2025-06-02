// Network Monitor - Include in Dev Tools
// This will log all network requests to help debug API issues

// Save the original fetch function
const originalFetch = window.fetch;

// Override fetch with a logging version
window.fetch = async function(...args) {
  const url = args[0];
  const options = args[1] || {};
  
  console.log(`🔍 Fetch request to: ${url}`, {
    method: options.method || 'GET',
    headers: options.headers || {}
  });
  
  // Call the original fetch
  try {
    const response = await originalFetch(...args);
    
    // Clone the response to read it twice (once for logging, once for the original caller)
    const clone = response.clone();
    
    // Log response data if it's JSON
    try {
      const data = await clone.json();
      console.log(`✅ Fetch response from ${url}:`, {
        status: response.status,
        data
      });
    } catch (e) {
      // Not JSON or can't be read
      console.log(`✅ Fetch response from ${url} (non-JSON):`, {
        status: response.status
      });
    }
    
    return response;
  } catch (error) {
    console.error(`❌ Fetch error for ${url}:`, error);
    throw error;
  }
};

// Save the original XMLHttpRequest.send
const originalXHRSend = XMLHttpRequest.prototype.send;
const originalXHROpen = XMLHttpRequest.prototype.open;

// Override XMLHttpRequest
XMLHttpRequest.prototype.open = function(method, url, ...rest) {
  this._url = url;
  this._method = method;
  return originalXHROpen.apply(this, [method, url, ...rest]);
};

XMLHttpRequest.prototype.send = function(body) {
  console.log(`🔍 XHR request to: ${this._url}`, {
    method: this._method,
    body: body || '(empty)'
  });
  
  // Add response listener
  this.addEventListener('load', function() {
    try {
      const responseData = this.responseText && JSON.parse(this.responseText);
      console.log(`✅ XHR response from ${this._url}:`, {
        status: this.status,
        data: responseData
      });
    } catch (e) {
      console.log(`✅ XHR response from ${this._url} (non-JSON):`, {
        status: this.status,
        text: this.responseText?.substring(0, 200) + (this.responseText?.length > 200 ? '...' : '')
      });
    }
  });
  
  this.addEventListener('error', function(error) {
    console.error(`❌ XHR error for ${this._url}:`, error);
  });
  
  return originalXHRSend.apply(this, arguments);
};

console.log('🛠️ Network monitoring activated. All fetch and XHR requests will be logged.');
