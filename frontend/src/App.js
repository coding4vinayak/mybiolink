import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Set up axios defaults
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Auth Context
const AuthContext = React.createContext();

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/me`);
      setUser(response.data);
    } catch (error) {
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/login`, { email, password });
      const { access_token, user } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(user);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Login failed' };
    }
  };

  const signup = async (email, username, password) => {
    try {
      const response = await axios.post(`${API}/signup`, { email, username, password });
      const { access_token, user } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(user);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Signup failed' };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, login, signup, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Components
const AuthForm = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ email: '', username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, signup } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = isLogin 
      ? await login(formData.email, formData.password)
      : await signup(formData.email, formData.username, formData.password);

    if (!result.success) {
      setError(result.error);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">LinkBio</h1>
          <p className="text-gray-600">Create your perfect link-in-bio page</p>
        </div>

        <div className="flex mb-6 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setIsLogin(true)}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              isLogin ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'
            }`}
          >
            Login
          </button>
          <button
            onClick={() => setIsLogin(false)}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              !isLogin ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'
            }`}
          >
            Sign Up
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <input
              type="email"
              placeholder="Email"
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>

          {!isLogin && (
            <div>
              <input
                type="text"
                placeholder="Username (for your link: /username)"
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              />
            </div>
          )}

          <div>
            <input
              type="password"
              placeholder="Password"
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            />
          </div>

          {error && (
            <div className="text-red-600 text-sm bg-red-50 p-3 rounded-lg">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Loading...' : (isLogin ? 'Login' : 'Sign Up')}
          </button>
        </form>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const { user, logout } = useAuth();
  const [linkPage, setLinkPage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [newLink, setNewLink] = useState({ title: '', url: '', icon: '🔗' });
  const [showAddLink, setShowAddLink] = useState(false);

  useEffect(() => {
    fetchLinkPage();
  }, []);

  const fetchLinkPage = async () => {
    try {
      const response = await axios.get(`${API}/linkpage/my`);
      setLinkPage(response.data);
    } catch (error) {
      if (error.response?.status === 404) {
        // Create initial link page
        await createLinkPage();
      }
    } finally {
      setLoading(false);
    }
  };

  const createLinkPage = async () => {
    try {
      const response = await axios.post(`${API}/linkpage`, {
        title: `${user.username}'s Links`,
        description: 'Check out my links!',
        theme_color: '#3B82F6'
      });
      setLinkPage(response.data);
    } catch (error) {
      console.error('Error creating link page:', error);
    }
  };

  const addLink = async () => {
    if (!newLink.title || !newLink.url) return;
    
    try {
      await axios.post(`${API}/linkpage/links`, newLink);
      setNewLink({ title: '', url: '', icon: '🔗' });
      setShowAddLink(false);
      fetchLinkPage();
    } catch (error) {
      console.error('Error adding link:', error);
    }
  };

  const deleteLink = async (linkId) => {
    try {
      await axios.delete(`${API}/linkpage/links/${linkId}`);
      fetchLinkPage();
    } catch (error) {
      console.error('Error deleting link:', error);
    }
  };

  const updateTheme = async (color) => {
    try {
      await axios.put(`${API}/linkpage`, { theme_color: color });
      fetchLinkPage();
    } catch (error) {
      console.error('Error updating theme:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  const publicUrl = `${window.location.origin}/${user.username}`;

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold text-gray-900">LinkBio Dashboard</h1>
            <p className="text-sm text-gray-600">Welcome back, {user.username}!</p>
          </div>
          <button
            onClick={logout}
            className="text-gray-600 hover:text-gray-900 text-sm"
          >
            Logout
          </button>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto p-4 grid md:grid-cols-2 gap-8">
        {/* Editor */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold mb-4">Your Public Link</h2>
            <div className="bg-gray-50 p-3 rounded-lg">
              <a 
                href={publicUrl} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 break-all"
              >
                {publicUrl}
              </a>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold mb-4">Theme Colors</h2>
            <div className="flex space-x-3">
              {['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899'].map(color => (
                <button
                  key={color}
                  onClick={() => updateTheme(color)}
                  className="w-10 h-10 rounded-full border-2 border-gray-200 hover:scale-110 transition-transform"
                  style={{ backgroundColor: color }}
                />
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Links</h2>
              <button
                onClick={() => setShowAddLink(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700"
              >
                Add Link
              </button>
            </div>

            {showAddLink && (
              <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                <div className="space-y-3">
                  <input
                    type="text"
                    placeholder="Link title"
                    className="w-full px-3 py-2 border rounded-lg"
                    value={newLink.title}
                    onChange={(e) => setNewLink({ ...newLink, title: e.target.value })}
                  />
                  <input
                    type="url"
                    placeholder="https://..."
                    className="w-full px-3 py-2 border rounded-lg"
                    value={newLink.url}
                    onChange={(e) => setNewLink({ ...newLink, url: e.target.value })}
                  />
                  <input
                    type="text"
                    placeholder="🔗 Icon (emoji)"
                    className="w-full px-3 py-2 border rounded-lg"
                    value={newLink.icon}
                    onChange={(e) => setNewLink({ ...newLink, icon: e.target.value })}
                  />
                  <div className="flex space-x-2">
                    <button
                      onClick={addLink}
                      className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-green-700"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => setShowAddLink(false)}
                      className="bg-gray-500 text-white px-4 py-2 rounded-lg text-sm hover:bg-gray-600"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}

            <div className="space-y-3">
              {linkPage?.links?.map((link) => (
                <div key={link.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <span className="text-xl">{link.icon}</span>
                    <div>
                      <div className="font-medium">{link.title}</div>
                      <div className="text-sm text-gray-600 truncate">{link.url}</div>
                    </div>
                  </div>
                  <button
                    onClick={() => deleteLink(link.id)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Delete
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Preview */}
        <div className="sticky top-4">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold mb-4">Preview</h2>
            <div className="border rounded-lg p-6 max-w-sm mx-auto" style={{ backgroundColor: '#f8fafc' }}>
              <div className="text-center mb-6">
                <div 
                  className="w-20 h-20 rounded-full mx-auto mb-4 flex items-center justify-center text-2xl font-bold text-white"
                  style={{ backgroundColor: linkPage?.theme_color || '#3B82F6' }}
                >
                  {user.username[0].toUpperCase()}
                </div>
                <h3 className="text-xl font-bold text-gray-900">{linkPage?.title}</h3>
                <p className="text-gray-600 text-sm">{linkPage?.description}</p>
              </div>
              
              <div className="space-y-3">
                {linkPage?.links?.map((link) => (
                  <div
                    key={link.id}
                    className="flex items-center p-3 bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow"
                  >
                    <span className="text-xl mr-3">{link.icon}</span>
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">{link.title}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const PublicPage = ({ username }) => {
  const [linkPage, setLinkPage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchPublicPage();
  }, [username]);

  const fetchPublicPage = async () => {
    try {
      const response = await axios.get(`${API}/linkpage/${username}`);
      setLinkPage(response.data);
    } catch (error) {
      setError('Page not found');
    } finally {
      setLoading(false);
    }
  };

  const handleLinkClick = async (link) => {
    // Track click
    try {
      await axios.post(`${API}/linkpage/links/${link.id}/click`);
    } catch (error) {
      console.error('Error tracking click:', error);
    }
    
    // Open link
    window.open(link.url, '_blank');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Page Not Found</h1>
          <p className="text-gray-600">The link page you're looking for doesn't exist.</p>
        </div>
      </div>
    );
  }

  return (
    <div 
      className="min-h-screen py-8 px-4"
      style={{ backgroundColor: linkPage.theme_color + '10' }}
    >
      <div className="max-w-md mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="text-center mb-8">
            <div 
              className="w-24 h-24 rounded-full mx-auto mb-4 flex items-center justify-center text-3xl font-bold text-white"
              style={{ backgroundColor: linkPage.theme_color }}
            >
              {linkPage.username[0].toUpperCase()}
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">{linkPage.title}</h1>
            <p className="text-gray-600">{linkPage.description}</p>
          </div>
          
          <div className="space-y-4">
            {linkPage.links.map((link) => (
              <button
                key={link.id}
                onClick={() => handleLinkClick(link)}
                className="w-full flex items-center p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors text-left group"
              >
                <span className="text-2xl mr-4">{link.icon}</span>
                <div className="flex-1">
                  <div className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                    {link.title}
                  </div>
                </div>
              </button>
            ))}
          </div>
          
          <div className="text-center mt-8 pt-6 border-t border-gray-200">
            <p className="text-gray-500 text-sm">
              Create your own link page with <span className="font-semibold">LinkBio</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

const App = () => {
  const [currentPage, setCurrentPage] = useState('');
  const { user, loading } = useAuth();

  useEffect(() => {
    const path = window.location.pathname;
    if (path === '/') {
      setCurrentPage('home');
    } else if (path.startsWith('/') && path.length > 1) {
      const username = path.substring(1);
      // Only treat as public page if it's not a logged-in user viewing their own page
      setCurrentPage(`public:${username}`);
    }
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  // Public page route - check this BEFORE checking authentication
  if (currentPage.startsWith('public:')) {
    const username = currentPage.split(':')[1];
    if (username && username.trim() !== '') {
      return <PublicPage username={username} />;
    }
  }

  // Main app logic - only show auth form if user is not logged in AND not viewing a public page
  if (!user && currentPage === 'home') {
    return <AuthForm />;
  }

  // If user is logged in, show dashboard
  if (user) {
    return <Dashboard />;
  }

  // Default fallback
  return <AuthForm />;
};

const AppWithAuth = () => {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
};

export default AppWithAuth;