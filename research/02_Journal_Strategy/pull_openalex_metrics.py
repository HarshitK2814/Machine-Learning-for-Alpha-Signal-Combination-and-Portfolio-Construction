import json, urllib.request, urllib.parse, time
journals = ["Journal of Finance","Review of Financial Studies","Journal of Financial Economics","Journal of Financial and Quantitative Analysis","Management Science","Operations Research","Review of Finance","Review of Asset Pricing Studies","Quantitative Finance","Journal of Computational Finance","Mathematical Finance","Journal of Banking and Finance","Journal of Financial Markets","Journal of Empirical Finance","International Journal of Forecasting","European Journal of Operational Research","Journal of Portfolio Management","Journal of Financial Econometrics","Journal of Econometrics","Journal of Financial Data Science","Critical Finance Review","Financial Analysts Journal","Journal of Business & Economic Statistics","Annals of Operations Research","Journal of Economic Dynamics and Control","Expert Systems with Applications","INFORMS Journal on Computing","SIAM Journal on Financial Mathematics","Finance and Stochastics","Journal of Machine Learning Research","Journal of Risk"]
out=[]
for j in journals:
    url="https://api.openalex.org/sources?search="+urllib.parse.quote(j)+"&per_page=3&mailto=research@example.org"
    try:
        d=json.load(urllib.request.urlopen(url,timeout=30))
        for r in d["results"][:2]:
            s=r.get("summary_stats",{})
            out.append(dict(query=j,name=r["display_name"],issn=r.get("issn_l"),publisher=r.get("host_organization_name"),works=r.get("works_count"),cites=r.get("cited_by_count"),two_yr_mean=s.get("2yr_mean_citedness"),h=s.get("h_index")))
    except Exception as e:
        out.append(dict(query=j,error=str(e)))
    time.sleep(0.2)
json.dump(out,open("openalex_journals.json","w"),indent=1)
for o in out: print(o)
