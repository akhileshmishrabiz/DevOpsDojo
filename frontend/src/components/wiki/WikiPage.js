import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { fetchWikiPage, deleteWikiPage } from '../../services/wikiService';

function WikiPage() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [page, setPage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    const loadPage = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const pageData = await fetchWikiPage(slug);
        setPage(pageData);
      } catch (err) {
        console.error(`Error loading wiki page ${slug}:`, err);
        setError('Failed to load the requested wiki page. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    loadPage();
  }, [slug]);

  const handleEdit = () => {
    navigate(`/wiki/edit/${slug}`);
  };

  const handleDelete = async () => {
    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }
    
    try {
      await deleteWikiPage(slug);
      navigate('/wiki');
    } catch (err) {
      setError(`Failed to delete page: ${err.message}`);
    }
  };

  const cancelDelete = () => {
    setConfirmDelete(false);
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <p>Loading wiki page...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <p>{error}</p>
          <Link to="/wiki" className="text-blue-600 underline mt-2 inline-block">
            Return to Wiki Home
          </Link>
        </div>
      </div>
    );
  }

  if (!page) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <p>Page not found</p>
          <Link to="/wiki" className="text-blue-600 underline mt-2 inline-block">
            Return to Wiki Home
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">{page.title}</h1>
          <div className="space-x-2">
            <button
              onClick={handleEdit}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors"
            >
              Edit
            </button>
            <button
              onClick={handleDelete}
              className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 transition-colors"
            >
              Delete
            </button>
          </div>
        </div>
        
        {confirmDelete && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            <p className="font-bold">Are you sure you want to delete this page?</p>
            <p className="mb-2">This action cannot be undone.</p>
            <div className="flex space-x-2 mt-2">
              <button
                onClick={handleDelete}
                className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors"
              >
                Yes, Delete
              </button>
              <button
                onClick={cancelDelete}
                className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
        
        <div className="flex items-center text-sm text-gray-600 mb-6">
          <span className="bg-gray-200 px-2 py-1 rounded">
            {page.category}
          </span>
          <span className="mx-4">
            Last updated: {new Date(page.updated_at).toLocaleDateString()}
          </span>
        </div>
        
        <div className="prose max-w-none">
          <ReactMarkdown>{page.content}</ReactMarkdown>
        </div>
        
        <div className="mt-6 pt-6 border-t">
          <Link
            to="/wiki"
            className="text-blue-600 hover:text-blue-800"
          >
            ← Back to Wiki Home
          </Link>
        </div>
      </div>
    </div>
  );
}

export default WikiPage;