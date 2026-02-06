"""
Utility functions for the core application.
"""


def get_site_from_context(request=None, site_domain=None):
    """
    Get site information from various contexts.
    Handles both sync (with request) and async (Celery) contexts.
    
    Priority:
    1. Extract from site_domain (if provided - usually from services)
    2. Extract from request (if provided - from views)
    3. Fall back to Site.objects.get_current() (for async tasks)
    
    Args:
        request: HTTP request object (from views)
        site_domain: Domain string (usually passed from services to async tasks)
                     Can include protocol (e.g., "https://comuniza.org")
    
    Returns:
        Site object from django.contrib.sites.models
    
    Example:
        # In a view:
        site = get_site_from_context(request=request)
        
        # In an async task:
        site = get_site_from_context(site_domain=context.get('site_domain'))
        
        # Fallback:
        site = get_site_from_context()
    """
    if site_domain:
        from django.contrib.sites.models import Site
        try:
            # Remove protocol if present to get clean domain
            clean_domain = site_domain
            if clean_domain.startswith('http://') or clean_domain.startswith('https://'):
                clean_domain = clean_domain.split('://', 1)[1]
            return Site.objects.get(domain=clean_domain)
        except Site.DoesNotExist:
            pass
    
    if request:
        from django.contrib.sites.shortcuts import get_current_site
        return get_current_site(request)
    
    # Async context or no request provided
    from django.contrib.sites.models import Site
    return Site.objects.get_current()
