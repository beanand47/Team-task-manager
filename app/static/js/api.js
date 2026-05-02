(function () {
  const TOKEN_KEY = "access_token";

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  async function apiCall(method, url, body) {
    const headers = { "Accept": "application/json" };
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
    if (body !== undefined && body !== null) headers["Content-Type"] = "application/json";

    const response = await fetch(url, {
      method,
      headers,
      body: body !== undefined && body !== null ? JSON.stringify(body) : undefined,
    });

    if (response.status === 401 && !["/login", "/signup"].includes(window.location.pathname)) {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem("user");
      window.location.href = "/login";
      throw new Error("Unauthorized");
    }

    if (!response.ok) {
      let message = `Request failed with status ${response.status}`;
      try {
        const error = await response.json();
        message = error.detail || message;
      } catch (_error) {}
      throw new Error(message);
    }

    if (response.status === 204) return null;
    return response.json();
  }

  window.apiCall = apiCall;
  window.apiGet = (url) => apiCall("GET", url);
  window.apiPost = (url, body) => apiCall("POST", url, body);
  window.apiPut = (url, body) => apiCall("PUT", url, body);
  window.apiDelete = (url) => apiCall("DELETE", url);
})();
