###########################################################
### make sure administrator is on localhost
############################################################


import os, socket, datetime,copy
import gluon.contenttype
import gluon.fileutils
### crytical --- make a copy of the environment
global_env=copy.copy(globals())
global_env['datetime']=datetime
http_host = request.env.http_host.split(':')[0]
remote_addr = request.env.remote_addr
try: hosts=(http_host, socket.gethostbyname(remote_addr))
except: hosts=(http_host,)
if remote_addr not in hosts:
    pass #raise HTTP(400)
if not gluon.fileutils.check_credentials(request):
    redirect('/admin')

response.view='appadmin.html'
response.menu=[[T('design'),False,URL('admin','default','design',
                args=[request.application])],
               [T('db'),False,URL(r=request,f='index')],
               [T('state'),False,URL(r=request,f='state')]]

###########################################################
### auxiliary functions
############################################################

def get_databases(request):
    dbs={}
    for key,value in global_env.items():
        cond=False
        try: cond=isinstance(value,GQLDB)
        except: cond=isinstance(value,SQLDB)
        if cond: dbs[key]=value
    return dbs

databases=get_databases(None)

def eval_in_global_env(text):
    exec('_ret=%s'%text,{},global_env)
    return global_env['_ret']

def get_database(request):
    if request.args and request.args[0] in databases:
        return eval_in_global_env(request.args[0])
    else:
        session.flash=T('invalid request')
        redirect(URL(r=request,f='index'))

def get_table(request):
    db=get_database(request)
    if len(request.args)>1 and request.args[1] in db.tables:
        return db,request.args[1]
    else:
        session.flash=T('invalid request')
        redirect(URL(r=request,f='index'))

def get_query(request):
    try:
        return eval_in_global_env(request.vars.query)
    except Exception:
        return None

###########################################################
### list all databases and tables
############################################################

def index():    
    return dict(databases=databases)

###########################################################
### insert a new record
############################################################

def insert():
    db,table=get_table(request)
    form=SQLFORM(db[table])
    if form.accepts(request.vars,session):
        response.flash=T('new record inserted')
    return dict(form=form)

###########################################################
### list all records in table and insert new record
############################################################

def download():
    import os
    db=get_database(request)
    filename=request.args[1]
    print filename
    ### for GAE only ###
    table,field=filename.split('.')[:2]
    if table in db.tables and field in db[table].fields:
        uploadfield=db[table][field].uploadfield
        if isinstance(uploadfield,str):
            from gluon.contenttype import contenttype
            response.headers['Content-Type']=contenttype(filename)
            rows=db(db[table][field]==filename).select()
            return rows[0][uploadfield]
    ### end for GAE ###
    path=os.path.join(request.folder,'uploads/',filename)
    return response.stream(open(path,'rb'))

def csv():
    import gluon.contenttype
    response.headers['Content-Type']=gluon.contenttype.contenttype('.csv')
    query=get_query(request)
    if not query: return None
    response.headers['Content-disposition']="attachment; filename=%s_%s.csv"%\
        tuple(request.vars.query.split('.')[:2])
    return str(db(query).select())

def import_csv(table,file):
    import csv
    reader = csv.reader(file)
    colnames=None
    for line in reader:
        if not colnames: 
            colnames=[x[x.find('.')+1:] for x in line]
            c=[i for i in range(len(line)) if colnames[i]!='id']            
        else:
            items=[(colnames[i],line[i]) for i in c]
            table.insert(**dict(items))

def select():
    import re
    db=get_database(request)
    dbname=request.args[0]
    regex=re.compile('(?P<table>\w+)\.(?P<field>\w+)=(?P<value>\d+)')
    if request.vars.query:
        match=regex.match(request.vars.query)
        if match: request.vars.query='%s.%s.%s==%s' % (request.args[0],match.group('table'),match.group('field'),match.group('value'))
    else:
        request.vars.query=session.last_query
    query=get_query(request)
    if request.vars.start: start=int(request.vars.start)
    else: start=0
    nrows=0
    stop=start+100
    table=None
    rows=[]
    orderby=request.vars.orderby
    if orderby:
        orderby=dbname+'.'+orderby
        if orderby==session.last_orderby:
           if orderby[0]=='~': orderby=orderby[1:]
           else: orderby='~'+orderby    
    session.last_orderby=orderby
    session.last_query=request.vars.query
    form=FORM(TABLE(TR('Query:','',INPUT(_style='width:400px',_name='query',_value=request.vars.query or '',requires=IS_NOT_EMPTY())),
                    TR('Update:',INPUT(_name='update_check',_type='checkbox',value=False),
                                 INPUT(_style='width:400px',_name='update_fields',_value=request.vars.update_fields or '')),
                    TR('Delete:',INPUT(_name='delete_check',_class='delete',_type='checkbox',value=False),''),
                    TR('','',INPUT(_type='submit',_value='submit'))))
    if request.vars.csvfile!=None:        
        try:
            import_csv(db[request.vars.table],request.vars.csvfile.file)
            response.flash=T('data uploaded')
        except: 
            response.flash=T('unable to parse csv file')
    if form.accepts(request.vars,formname=None):
        regex=re.compile(request.args[0]+'\.(?P<table>\w+)\.id\>0')
        match=regex.match(form.vars.query.strip())
        if match: table=match.group('table')
        try:
            nrows=db(query).count()
            if form.vars.update_check and form.vars.update_fields:
                db(query).update(**eval_in_global_env('dict(%s)'%form.vars.update_fields))
                response.flash=T('%s rows updated',nrows)
            elif form.vars.delete_check:
                db(query).delete()
                response.flash=T('%s rows deleted',nrows)
            nrows=db(query).count()
            if orderby: rows=db(query).select(limitby=(start,stop), orderby=eval_in_global_env(orderby))
            else: rows=db(query).select(limitby=(start,stop))
        except:
            rows,nrows=[],0
            response.flash=T('Invalid Query')
    return dict(form=form,table=table,start=start,stop=stop,nrows=nrows,rows=rows,query=request.vars.query)

###########################################################
### edit delete one record
############################################################

def update():
    db,table=get_table(request)
    try:
        id=int(request.args[2])
        record=db(db[table].id==id).select()[0]
    except:
        session.flash=T('record does not exist')
        redirect(URL(r=request,f='select',args=request.args[:1],vars=dict(query='%s.%s.id>0'%tuple(request.args[:2]))))
    form=SQLFORM(db[table],record,deletable=True,
                 linkto=URL(r=request,f='select',args=request.args[:1]),
                 upload=URL(r=request,f='download',args=request.args[:1]))
    if form.accepts(request.vars,session): 
        response.flash=T('done!')
        redirect(URL(r=request,f='select',args=request.args[:1],vars=dict(query='%s.%s.id>0'%tuple(request.args[:2]))))
    return dict(form=form)

###########################################################
### get global variables
############################################################

def state(): return dict()