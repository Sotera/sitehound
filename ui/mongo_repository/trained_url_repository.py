import pymongo
from bson import ObjectId

from ui.singleton import Singleton


def get_seeds_urls_by_source_dao(workspace_id, source, relevance, last_id):

    source_search_conditions = []
    if source == "searchengine":
        source_search_conditions.append({'crawlEntityType': "BING"})
        source_search_conditions.append({'crawlEntityType': "GOOGLE"})
    elif source == "twitter":
        source_search_conditions.append({'crawlEntityType': "TWITTER"})
    elif source == "tor":
        source_search_conditions.append({'crawlEntityType': "TOR"})
    elif source == "imported":
        source_search_conditions.append({'crawlEntityType': "MANUAL"})
    elif source == "deepdeep":
        source_search_conditions.append({'crawlEntityType': "DD"})
    else:
        print("no valid source was provided:" + source)
    source_search_object = {'$or': source_search_conditions}

    relevance_search_conditions = []
    if "neutral" in relevance and relevance['neutral']:
        relevance_search_conditions.append({'relevant': None})
    if "relevant" in relevance and relevance['relevant']:
        relevance_search_conditions.append({'relevant': True})
    if "irrelevant" in relevance and relevance['irrelevant']:
        relevance_search_conditions.append({'relevant': False})
    relevance_search_object = {'$or': relevance_search_conditions}

    page_search_object = {}
    if last_id is not None:
        # page_search_object = {'_id' > input_search_query['last_id']}
        page_search_object = {"_id": {"$gt": ObjectId(last_id)}}

    deleted_search_object = {'deleted': None}
    workspace_search_object = {'workspaceId': workspace_id}

    # field_names_to_include = ['_id', 'host', 'desc', 'crawlEntityType', 'url', 'words', 'urlDesc', 'categories', 'language', 'relevant']
    # field_names_to_include = ['_id', 'crawlEntityType', 'url', 'relevant', 'words']
    # field_names_to_include = ['_id', 'crawlEntityType', 'url', 'relevant']
    field_names_to_include = ['_id', 'host', 'desc', 'crawlEntityType', 'url', 'words', 'title', 'categories', 'language', 'relevant']

    collection = Singleton.getInstance().mongo_instance.get_seed_urls_collection()
    res = collection\
        .find({'$and': [source_search_object, relevance_search_object, page_search_object, deleted_search_object, workspace_search_object]}, field_names_to_include)\
        .sort('_id', pymongo.ASCENDING)\
        .limit(3)

    docs = list(res)
    return docs


def get_seeds_urls_by_workspace_dao(workspace_id):
    collection = Singleton.getInstance().mongo_instance.get_seed_urls_collection()
    return list(collection.find({'workspaceId': workspace_id}))


' retrieves only the field url from the docs '


def get_seeds_urls_url(workspace_id):
    collection = Singleton.getInstance().mongo_instance.get_seed_urls_collection()
    res = collection.find({'workspaceId': workspace_id}, {'_id': 0, 'url': 1})
    docs = list(res)
    return docs


def get_seeds_urls_categorized(workspace_id):
    collection = Singleton.getInstance().mongo_instance.get_seed_urls_collection()
    relevant_urls_result = collection.find({'workspaceId': workspace_id, 'relevant': True, 'deleted': {'$exists': False}}, {'_id': 0, 'url': 1})
    relevant_urls = []
    for url_doc in relevant_urls_result:
        if 'url' in url_doc:
            relevant_urls.append(url_doc['url'])

    irrelevant_urls_result = collection.find({'relevant': False, 'deleted': {'$exists': False}}, {'_id': 0, 'url': 1})
    irrelevant_urls = []
    for url_doc in irrelevant_urls_result:
        if 'url' in url_doc:
            irrelevant_urls.append(url_doc['url'])

    return {'relevant': list(relevant_urls), 'irrelevant': list(irrelevant_urls)}






################ SAVE_CUSTOMIZE_SEEDS #########################

# def dao_insert_url(url, is_relevant):
#     extracted = extract_tld(url)
#     host = extracted.domain + '.' + extracted.suffix
#     update_object = {"host": host, "relevant": is_relevant}
#
#     collection = Singleton.getInstance().mongo_instance.get_current_seed_urls_collection()
#     collection.update({"url": url}, {'$set': update_object}, True)


def dao_update_relevance(url, obj):
    update_object = {}
    update_object['relevant'] = obj['relevant']
    collection = Singleton.getInstance().mongo_instance.get_current_seed_urls_collection()
    print "setting url %s to %s in collection %s" % (url, str(obj['relevant']), collection)
    collection.update({"url": url}, {'$set': update_object}, True)


def dao_update_relevanceByid(workspace_id, id, relevance):
    collection = Singleton.getInstance().mongo_instance.get_seed_urls_collection()
    update_object= {}
    update_object['relevant'] = relevance
    collection.update({"_id": ObjectId(id)}, {'$set': update_object}, True)


def dao_delete_seed_url(workspace_id, id):
    collection = Singleton.getInstance().mongo_instance.get_seed_urls_collection()
    update_object= {}
    update_object['deleted'] = True
    collection.update({"_id": ObjectId(id)}, {'$set': update_object}, True)


def dao_reset_results(workspace_id, source):

    collection = Singleton.getInstance().mongo_instance.get_seed_urls_collection()

    source_search_conditions = []

    workspace_search_object = {'workspaceId': workspace_id}

    if source == "searchengine":
        source_search_conditions.append({'crawlEntityType': "BING"})
        source_search_conditions.append({'crawlEntityType': "GOOGLE"})
    elif source == "twitter":
        source_search_conditions.append({'crawlEntityType': "TWITTER"})
    elif source == "tor":
        source_search_conditions.append({'crawlEntityType': "TOR"})
    elif source == "imported":
        source_search_conditions.append({'crawlEntityType': "MANUAL"})
    elif source == "deepdeep":
        source_search_conditions.append({'crawlEntityType': "DD"})
    else:
        print("no valid source was provided:" + source)
        return
    source_search_object = {'$or': source_search_conditions}

    collection.remove({'$and': [workspace_search_object, source_search_object]})


def dao_aggregate_urls(workspace_id):

    collection = Singleton.getInstance().mongo_instance.get_seed_urls_collection()
    source_search_conditions = []
    workspace_search_object = {'workspaceId': workspace_id}
    delete_search_object = {'deleted': {'$exists': False}}
    # 'deleted': {'$exists': False}}
    source_search_conditions.append(workspace_search_object)
    source_search_conditions.append(delete_search_object)

    source_search_object = {'$and': source_search_conditions}

    try:
        res = collection.aggregate([

            # '$group': {'_id': '$crawlEntityType', "count": {"$sum": 1}}
            {'$match': source_search_object},
            {'$group': {'_id': {'crawlEntityType': '$crawlEntityType', 'relevant': '$relevant'}, "count": {"$sum": 1}}}
        ])
    except Exception as e:
        print e

    return res["result"]


