from django.shortcuts import render
from main_app.forms import *
import re
import urllib.request
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.cache import cache_page

def find_readme(readme_find,data):
    '''finds readme from a given data which is
       scraped from a url.

       readme_find - index where the readme in HTMl begins.
       data - data where readme is looked for
    '''
    data = data[readme_find.end():]
    readme_start = re.search('<p>',data).end()
    readme_end = re.search('</article>',data).start()
    readme = data[readme_start:readme_end]
    return readme

@cache_page(60*60)   # caches the view for an hour. diff searches have diff cache
def search(request):
    ''' Searches for repositories
        if searched URL belongs to an organization.
        opens a readme if the url belongs to a repo.
    '''    

    results = None
    search_url = None

    if request.GET.get('query') :
        search_url  = request.GET.get('query')
        print(search_url)

        url = search_url.split('.com/')
        url = url[1]
        url = url.split('/')

        # checks if url is of a repo or an org
        if len(url) > 1:
            cont = 'repo'
        else:
            cont = 'org'

        # If enetered URL belongs to an org
        if cont == 'org':
            # getting data
            try:
                # gets data from the url
                data = urllib.request.urlopen(search_url).read()
                data = data.decode("utf-8")

            except:
                return redirect(request.META.get('HTTP_REFERER'))    

            flag = 1
            repo_end = 0
            results = []

            # finds all repos and appends to results
            while flag:

                # strips data so that re.search doesn't searches
                # already searched repo names.
                data = data[repo_end:]

                try:
                    # starting index for a repo name
                    repo_start = re.search('itemprop="name codeRepository">',data).end()

                    data = data[repo_start:]

                    # end index for the repo name
                    repo_end = re.search('</a>',data).start()

                    repo = data[:repo_end]
                    # result is the string between two searches
                    results.append(repo.strip())

                except:
                    # stops searching when no more results found.
                    flag = 0

        # If Entered URL belongs to a repository
        if cont =='repo':
            try:
                # gets data 
                data = urllib.request.urlopen(search_url).read()
                data = data.decode("utf-8")

            except:
                return redirect(request.META.get('HTTP_REFERER'))    

            # This looks for the readme box which is displayed on the home directory
            readme_find = re.search('<div id="readme"', data)

            # if the readme box is present
            if readme_find:
                # scrapes the readme as it is and returns it 
                readme = find_readme(readme_find, data)

                return HttpResponse( "<h1>README</h1>" + readme)

            else:
                # if readme is present in the docs directory
                docs_find = re.search('title="docs"', data)

                if docs_find:
                    data = data[docs_find.end():]
                    
                    url_start = re.search('href="',data).end()
                    url_end = re.search('">',data).start()
                    url = data[url_start:url_end]

                    # gets data from the docs' directory
                    data = urllib.request.urlopen("https://github.com/"+url).read()
                    data = data.decode("utf-8")

                    # now finds the readme table on this page
                    readme_find = re.search('<div id="readme"', data)
                    
                    # if the table is present
                    if readme_find:
                        readme = find_readme(readme_find, data)
                        return HttpResponse( "<h1>README</h1>" + readme)
                    # If readme is not present on this directory as well

                    else:
                        readme = "<h2>NO README FOUND</h2>"
                        return HttpResponse(readme)

                else:
                    readme = "<h2>NO README FOUND</h2>"
                    return HttpResponse(readme)


    return render(request, 'main_app/base.html',
                  context={'results':results, 
                  'query':search_url})
