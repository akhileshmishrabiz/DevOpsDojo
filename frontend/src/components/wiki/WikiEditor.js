import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { 
  fetchWikiPage, 
  createWikiPage, 
  updateWikiPage, 
  fetchWikiCategories 
} from '../../services/wikiService';

function WikiEditor() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const isEditMode = !!slug;
  
  const [formData, setFormData] = useState({
    title: '',
    slug: '',
    content: '',
    category: ''
  });
  const [existingCategories, setExistingCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [previewMode, setPreviewMode] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Load categories
        const categories = await fetchWikiCategories();
        setExistingCategories(categories);
        
        // If in edit mode, load the page data
        if (isEditMode) {
          const pageData = await fetchWikiPage(slug);
          setFormData({
            title: pageData.title || '',
            slug: pageData.slug || '',
            content: pageData.content || '',
            category: pageData.category || ''
          });
        }
      } catch (err) {
        console.error('Error loading data:', err);
        setError('Failed to load page data. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [isEditMode, slug]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Auto-generate slug from title if in create mode
    if (name === 'title' && !isEditMode) {
      setFormData(prev => ({
        ...prev,
        slug: value.toLowerCase()
          .replace(/[^\w\s-]/g, '') // Remove special chars
          .replace(/\s+/g, '-')     // Replace spaces with hyphens
          .replace(/-+/g, '-')      // Replace multiple hyphens with single
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setSaving(true);
      setError(null);
      
      // Validate form
      if (!formData.title.trim()) {
        setError('Title is required');
        setSaving(false);
        return;
      }
      
      if (!formData.content.trim()) {
        setError('Content is required');
        setSaving(false);
        return;
      }
      
      if (!formData.category.trim()) {
        setError('Category is required');
        setSaving(false);
        return;
      }
      
      // Save page (create or update)
      if (isEditMode) {
        await updateWikiPage(slug, formData);
        navigate(`/wiki/${formData.slug}`);
      } else {
        const newPage = await createWikiPage(formData);
        navigate(`/wiki/${newPage.slug}`);
      }
    } catch (err) {
      setError(`Failed to save page: ${err.message}`);
      setSaving(false);
    }
  };

  const togglePreview = () => {
    setPreviewMode(!previewMode);
  };

  // Use this function if marked is loaded from CDN
  const renderMarkdown = (text) => {
    if (window.marked) {
      return { __html: window.marked.parse(text) };
    }
    // Fallback if marked is not available
    return { __html: text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\n/g, '<br>') 
    };
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h1 className="text-3xl font-bold mb-6">
          {isEditMode ? 'Edit Wiki Page' : 'Create New Wiki Page'}
        </h1>
        
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="title" className="block text-gray-700 font-medium mb-2">
              Title
            </label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              className="w-full p-2 border rounded"
              required
            />
          </div>
          
          <div className="mb-4">
            <label htmlFor="slug" className="block text-gray-700 font-medium mb-2">
              URL Slug
            </label>
            <div className="flex items-center">
              <span className="text-gray-500 mr-2">/wiki/</span>
              <input
                type="text"
                id="slug"
                name="slug"
                value={formData.slug}
                onChange={handleInputChange}
                className="flex-1 p-2 border rounded"
                required
              />
            </div>
            <p className="text-sm text-gray-500 mt-1">
              Used in the URL. Auto-generated from title, but you can customize it.
            </p>
          </div>
          
          <div className="mb-4">
            <label htmlFor="category" className="block text-gray-700 font-medium mb-2">
              Category
            </label>
            <div className="flex">
              <input
                type="text"
                id="category"
                name="category"
                value={formData.category}
                onChange={handleInputChange}
                list="categories"
                className="w-full p-2 border rounded"
                required
              />
              <datalist id="categories">
                {existingCategories.map(category => (
                  <option key={category} value={category} />
                ))}
              </datalist>
            </div>
            <p className="text-sm text-gray-500 mt-1">
              Choose an existing category or create a new one.
            </p>
          </div>
          
          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <label htmlFor="content" className="block text-gray-700 font-medium">
                Content (Markdown)
              </label>
              <button
                type="button"
                onClick={togglePreview}
                className="text-blue-500 hover:text-blue-700"
              >
                {previewMode ? 'Edit' : 'Preview'}
              </button>
            </div>
            
            {previewMode ? (
              // Two preview options - use what works best
              <div className="border rounded p-4 min-h-[300px] prose max-w-none">
                {/* Option 1: Using dangerouslySetInnerHTML with marked from CDN */}
                {window.marked ? (
                  <div dangerouslySetInnerHTML={renderMarkdown(formData.content)} />
                ) : (
                  /* Option 2: Using react-markdown */
                  <ReactMarkdown>{formData.content}</ReactMarkdown>
                )}
              </div>
            ) : (
              <textarea
                id="content"
                name="content"
                value={formData.content}
                onChange={handleInputChange}
                className="w-full p-2 border rounded font-mono"
                rows="15"
                required
              />
            )}
            
            <p className="text-sm text-gray-500 mt-1">
              Markdown formatting is supported. Use # for headings, * for lists, etc.
            </p>
          </div>
          
          <div className="flex justify-between">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 transition-colors disabled:bg-blue-300"
            >
              {saving ? 'Saving...' : 'Save Page'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default WikiEditor;