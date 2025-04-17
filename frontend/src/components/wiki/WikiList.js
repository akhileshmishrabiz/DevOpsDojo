import React, { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { fetchAllWikiPages, fetchWikiCategories } from '../../services/wikiService';

function WikiList() {
  const [pages, setPages] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { category } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch wiki pages (filtered by category if provided)
        const pagesData = await fetchAllWikiPages(category);
        setPages(Array.isArray(pagesData) ? pagesData : []);
        
        // Fetch categories for the sidebar
        const categoriesData = await fetchWikiCategories();
        setCategories(categoriesData);
        
      } catch (err) {
        console.error('Error loading wiki data:', err);
        setError('Failed to load wiki pages. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [category]);

  const handleCategorySelect = (selectedCategory) => {
    if (selectedCategory) {
      navigate(`/wiki/category/${selectedCategory}`);
    } else {
      navigate('/wiki');
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <p>Loading wiki pages...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col md:flex-row">
        {/* Sidebar - Categories */}
        <div className="w-full md:w-1/4 md:pr-8 mb-6 md:mb-0">
          <div className="bg-white rounded-lg shadow p-4">
            <h2 className="text-xl font-bold mb-4">Categories</h2>
            <ul className="space-y-2">
              <li>
                <button
                  onClick={() => handleCategorySelect(null)}
                  className={`block w-full text-left px-3 py-2 rounded hover:bg-blue-50 ${
                    !category ? 'bg-blue-100 font-medium' : ''
                  }`}
                >
                  All Pages
                </button>
              </li>
              {categories.map((cat) => (
                <li key={cat}>
                  <button
                    onClick={() => handleCategorySelect(cat)}
                    className={`block w-full text-left px-3 py-2 rounded hover:bg-blue-50 ${
                      category === cat ? 'bg-blue-100 font-medium' : ''
                    }`}
                  >
                    {cat.charAt(0).toUpperCase() + cat.slice(1)}
                  </button>
                </li>
              ))}
            </ul>
            
            <div className="mt-6">
              <Link
                to="/wiki/create"
                className="block w-full bg-blue-500 text-white text-center px-4 py-2 rounded hover:bg-blue-600 transition-colors"
              >
                Create New Page
              </Link>
            </div>
          </div>
        </div>
        
        {/* Main Content - Wiki Pages List */}
        <div className="w-full md:w-3/4">
          <div className="bg-white rounded-lg shadow p-6">
            <h1 className="text-3xl font-bold mb-6">
              {category 
                ? `${category.charAt(0).toUpperCase() + category.slice(1)} Pages` 
                : 'All Wiki Pages'}
            </h1>
            
            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                {error}
              </div>
            )}
            
            {pages.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500">
                  {category
                    ? `No pages found in the "${category}" category.`
                    : 'No wiki pages found.'}
                </p>
                <Link
                  to="/wiki/create"
                  className="inline-block mt-4 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors"
                >
                  Create First Page
                </Link>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4">
                {pages.map((page) => (
                  <div key={page.slug} className="border rounded-lg p-4 hover:bg-gray-50">
                    <Link to={`/wiki/${page.slug}`} className="block">
                      <h2 className="text-xl font-bold text-blue-600 hover:text-blue-800">
                        {page.title}
                      </h2>
                      <div className="flex items-center mt-2 text-sm text-gray-500">
                        <span className="bg-gray-200 px-2 py-1 rounded">
                          {page.category}
                        </span>
                        <span className="ml-4">
                          Last updated: {new Date(page.updated_at).toLocaleDateString()}
                        </span>
                      </div>
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default WikiList;