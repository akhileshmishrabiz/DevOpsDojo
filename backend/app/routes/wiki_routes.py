from flask import jsonify, request
from app.models.models import WikiPage
from app.models import db
from slugify import slugify
from . import wiki_bp
from datetime import datetime

@wiki_bp.route('', methods=['GET'])
def get_all_wiki_pages():
    """Get all wiki pages or filter by category"""
    category = request.args.get('category')
    
    try:
        if category:
            print(f"Filtering wiki pages by category: {category}")
            pages = WikiPage.query.filter_by(category=category).all()
            if not pages:
                print(f"No wiki pages found in category: {category}")
                return jsonify({
                    "message": f"No wiki pages found in category: {category}",
                    "pages": []
                })
        else:
            print("Retrieving all wiki pages")
            pages = WikiPage.query.all()
            if not pages:
                print("No wiki pages found")
                return jsonify({
                    "message": "No wiki pages found",
                    "pages": []
                })
        
        result = [page.to_dict() for page in pages]
        print(f"Returning {len(result)} wiki pages")
        return jsonify(result)
    
    except Exception as e:
        print(f"Error retrieving wiki pages: {str(e)}")
        return jsonify({"error": str(e)}), 500

@wiki_bp.route('/<string:slug>', methods=['GET'])
def get_wiki_page(slug):
    """Get a specific wiki page by slug"""
    page = WikiPage.query.filter_by(slug=slug).first_or_404()
    return jsonify(page.to_dict())

@wiki_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all unique wiki categories"""
    categories = db.session.query(WikiPage.category).distinct().all()
    return jsonify([category[0] for category in categories])

@wiki_bp.route('', methods=['POST'])
def create_wiki_page():
    """Create a new wiki page"""
    data = request.get_json()
    
    if not all(k in data for k in ('title', 'content', 'category')):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Create slug from title if not provided
    if 'slug' not in data or not data['slug']:
        data['slug'] = slugify(data['title'])
    else:
        data['slug'] = slugify(data['slug'])
    
    # Check if slug already exists
    existing_page = WikiPage.query.filter_by(slug=data['slug']).first()
    if existing_page:
        return jsonify({'error': f'A page with slug "{data["slug"]}" already exists'}), 400
    
    try:
        page = WikiPage(
            title=data['title'],
            slug=data['slug'],
            content=data['content'],
            category=data['category']
        )
        
        db.session.add(page)
        db.session.commit()
        return jsonify(page.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@wiki_bp.route('/<string:slug>', methods=['PUT'])
def update_wiki_page(slug):
    """Update an existing wiki page"""
    page = WikiPage.query.filter_by(slug=slug).first_or_404()
    data = request.get_json()
    
    if 'title' in data:
        page.title = data['title']
    if 'content' in data:
        page.content = data['content']
    if 'category' in data:
        page.category = data['category']
    
    # Update slug if title was changed and no custom slug was provided
    if 'title' in data and ('slug' not in data or not data['slug']):
        page.slug = slugify(data['title'])
    elif 'slug' in data and data['slug']:
        page.slug = slugify(data['slug'])
    
    # Check if the new slug already exists on a different page
    if page.slug != slug:
        existing_page = WikiPage.query.filter_by(slug=page.slug).first()
        if existing_page and existing_page.id != page.id:
            return jsonify({'error': f'A page with slug "{page.slug}" already exists'}), 400
    
    page.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify(page.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@wiki_bp.route('/<string:slug>', methods=['DELETE'])
def delete_wiki_page(slug):
    """Delete a wiki page"""
    page = WikiPage.query.filter_by(slug=slug).first_or_404()
    
    try:
        db.session.delete(page)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400  