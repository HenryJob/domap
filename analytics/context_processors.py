def tracking(request):
    return {
        'current_pageview': getattr(request, 'current_pageview', None),
    }
