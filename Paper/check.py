# -*- coding:gb2312 -*-

import zipfile
from lxml import etree
import re
import sys
import shutil
import time
import os
import tempfile

Input_DirPath = sys.argv[1]#�����ļ��е�·��,�����еĵڶ�������
Out_DirPath = sys.argv[2]#����ļ��е�·���������еĵ���������

Docx_Filename = Input_DirPath + 'test1.docx'
Rule_Filename = Input_DirPath + 'rules.txt'

word_schema='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
Unicode_bt ='gb2312'#�����ַ����뷽ʽ���ҵĻ�������gb2312������������utf-8�����и����������GBK

#����4�������ǹ��� ��ѹ��word�ĵ��Ͷ�ȡxml���ݲ����ڵ��ǩ�����νṹ���е���
def get_word_xml(docx_filename):
    zipF = zipfile.ZipFile(docx_filename)
    xml_content = zipF.read('word/document.xml')
    style_content=zipF.read('word/styles.xml')
    return xml_content,style_content

def get_xml_tree(xml_string):
    return etree.fromstring(xml_string)

def _iter(my_tree,type_char):
    for node in my_tree.iter(tag=etree.Element):
        if _check_element_is(node,type_char):
            yield node

def _check_element_is(element,type_char):
    return element.tag == '%s%s' % (word_schema,type_char)
 
#��ȡ�ڵ�������ı�����
def get_ptext(w_p):
    ptext = ''
#-modified by zqd 20160125-----------------------
    for node in w_p.iter(tag=etree.Element):
        if _check_element_is(node,'t'):
#-----------------------------------------------
            ptext += node.text
    return ptext.encode(Unicode_bt,'ignore')#�����������п��ܳ�����ֵĸ����޷������ַ������ͬѧ�������ط���ճ����������˼��ϸ�ignore�������ԷǷ��ַ�
def get_level(w_p):
    for pPr in w_p:
        if _check_element_is(pPr,'pPr'):
            for pPr_node in pPr:
                if _check_element_is(pPr_node,'outlineLvl'):
                    return pPr_node.get('%s%s' %(word_schema,'val'))
                
                if _check_element_is(pPr_node,'pStyle'):
                    style_xml = etree.fromstring(zipfile.ZipFile(Docx_Filename).read('word/styles.xml'))
                    styleID = pPr_node.get('%s%s' %(word_schema,'val'))
                    flag = 1
                    while flag == 1 :
                        #print 'style',styleID
                        flag = 0
                        for style in _iter(style_xml,'style'):
                            if style.get('%s%s' %(word_schema,'styleId')) == styleID:
                                for style_node in style:
                                    if _check_element_is(style_node,'pPr'):
                                        for pPr_node in style_node:
                                            if _check_element_is(pPr_node,'outlineLvl'):
                                                return pPr_node.get('%s%s' %(word_schema,'val'))
                                    if _check_element_is(style_node,'basedOn'):
                                        styleID = style_node.get('%s%s' %(word_schema,'val'))
                                        flag = 1               

#-----------------------------    
#����5���������� ��ȡ�ı���Ӧ�ĸ�ʽ��Ϣ
#��ʼ��һ����ʽ�ֵ䣬�ֶ�ֵ������Ϊ���㴦���Ϊstr��ֵ�Ķ���ͷ�Χ���Բο��ĵ�
def init_fd(d):
    d['fontCN']='����'
    d['fontEN']='Times New Roman'
    d['fontSize']='21'#��Ϊword��Ĭ����21
    d['paraAlign']='both'
    d['fontShape']='0'
    d['paraSpace']='240'
    d['paraIsIntent']='0'
    d['paraIsIntent1']='0'
    d['paraFrontSpace']='100'
    d['paraAfterSpace']='100'
    d['paraGrade']='0'
    return d

def has_key(node,attribute):
    return '%s%s' %(word_schema,attribute) in node.keys()

def get_val(node,attribute):
    if has_key(node,attribute):
        return node.get('%s%s' %(word_schema,attribute))
    else:
        return 'δ��ȡ����ֵ'

#��ȡ�ĸ�ʽ��Ϣ������ǰ�ڵ�ĸ�ʽ�ֵ�
def assign_fd(node,d):
    for detail in node.iter(tag=etree.Element):
#------20160314 zqd----------------------------------
        if _check_element_is(detail,'rFonts'):
            if has_key(detail,'eastAsia'):#�д�����
                d['fontCN'] = get_val(detail,'eastAsia').encode(Unicode_bt)
            elif has_key(detail,'ascii'):
                #print get_val(detail,'hAnsi')
                d['fontEN'] = get_val(detail,'ascii').encode(Unicode_bt)
#--------------------------------------------
        
        elif _check_element_is(detail,'sz'):
            d['fontSize'] = get_val(detail,'val')

        elif _check_element_is(detail,'jc'):
            d['paraAlign'] = get_val(detail,'val')

        elif _check_element_is(detail,'b'):
            if has_key(detail,'val'):
                if get_val(detail, 'val') != '0' and get_val(detail, 'val') != 'false':
                    d['fontShape'] = '1'#��ʾbold
                else:
                    #print 'not blod'
                    d['fontShape'] = '0'
            else:
                d['fontShape'] = '1'#��ʾbold

        elif _check_element_is(detail,'spacing'):
            if has_key(detail,'line'):
                d['paraSpace'] = get_val(detail,'line')
            if has_key(detail,'before'):
                d['paraFrontSpace']= get_val(detail,'before')
            if has_key(detail,'after'):
                d['paraAfterSpace']= get_val(detail,'after')
#--------20160313 zqd----------------------------------------
        elif _check_element_is(detail,'ind'):
            if has_key(detail,'firstLine'):
                d['paraIsIntent']=get_val(detail,'firstLine')
            if has_key(detail,'firstLine'):
                d['paraIsIntent1']=get_val(detail,'firstLineChars')
                #print d['paraIsIntent']
                #���������������ǲ�ͬ�ģ����忴xml�ĵ���firstLineChars���ȼ���
#-------------------------------------------------
        elif _check_element_is(detail,'outlineLvl'):
            d['paraGrade'] = get_val(detail,'val')

    return d
#----20160314 zqd------------
def get_style_format(styleID,d):
    for style in _iter(style_tree,'style'):
        if get_val(style,'styleId') == styleID:#get_val������
            for detail in style.iter(tag=etree.Element):
                if _check_element_is(detail,'basedOn'):
                    styleID1 = get_val(detail,'val')
                    get_style_format(styleID1,d)
                if _check_element_is(detail,'pPr'):
                    assign_fd(detail,d)
                if _check_element_is(detail,'rPr'):
                    assign_fd(detail,d)
            
#��ȡ��ʽ
def get_format(node,d):
    init_fd(d)
    for pPr in _iter(node,'pPr'):
        for pstyle in _iter(pPr,'pStyle'):
            styleID = get_val(pstyle,'val')
            get_style_format(styleID,d)
        assign_fd(pPr,d)

    return d
#--------------------------------------------------
def first_locate():
    paraNum = 0
    part[1] = 'cover'
    reference = []
    current_part = ''
    for paragr in _iter(xml_tree,'p'):
        paraNum +=1
        text=get_ptext(paragr)
        if not text or text == '' or text == '':
            continue
        #print text
        for r in paragr.iter(tag=etree.Element):
            if _check_element_is(r, 'r'):
                for instr in r.iter(tag=etree.Element):
                    if _check_element_is(instr, 'instrText'):
                        refer = False
                        if "REF _Ref" in instr.text:
                            refer = True
                        if refer is True:
                            reference.append((instr.text[9:].split())[0])
        if '��������' in text:
            current_part = part[paraNum] = 'statement'
        elif '�������պ����ѧ' in text  or '��������ҵ��ƣ����ģ�������' in text:
            current_part = part[paraNum] = 'taskbook'
        elif '���ķ����鼹' in text:
            current_part = part[paraNum] = 'spine'
        elif re.compile(r'ժ *Ҫ').match(text):
            current_part = part[paraNum] = 'abstract'
        elif 'Abstract' in text or 'abstract' in text or 'ABSTRACT' in text:
            current_part = part[paraNum] = 'abstract_en'
        elif re.compile(r'Ŀ *¼').match(text) or re.compile(r'ͼĿ¼').match(text) or re.compile(r'��Ŀ¼').match(text) or re.compile(r'ͼ��Ŀ¼').match(text):
            current_part = part[paraNum] = 'menu'
        elif (current_part == 'menu' and not text[-1].isdigit()) or( re.compile(r'.*�� *��').match(text) and not text[-1].isdigit()):
            current_part = part[paraNum] = 'body'
        elif text == '�ο�����':
            current_part = part[paraNum] = 'refer'
        elif text.startswith('��') and text.endswith('¼') :
            current_part = part[paraNum] = 'appendix'
    if not 'statement' in part.values():
        print 'warning statement doesnot exsit'
    if not 'spine' in part.values():
        print 'warning spine'
    if not 'abstract' in part.values():
        print 'warning abstract'
    if not 'body' in part.values():
        print 'warning body'
    if not 'menu' in part.values():
        print 'warning menu'
    return reference
def second_locate():
    paraNum = 0
    locate[1] = 'cover1'
    cur_part = ''
    cur_state = 'cover1'
    title = ''
    warnInfo=[]
    mentioned = []
    last_text = ''
    for paragr in _iter(xml_tree,'p'):
        paraNum +=1
        #------hsy add object detection July.13.2016--
        for node in paragr.iter(tag = etree.Element):
            if _check_element_is(node,'r'):
                for innode in node.iter(tag = etree.Element):
                    if _check_element_is(innode,'object'):
                        cur_state = locate[paraNum] = 'object'
            if _check_element_is(node,'bookmarkStart'):
                if node.values()[1][:4] == '_Ref':
                    if node.values()[1][4:] in reference:
                            mentioned.append(node.values()[1][4:])
        #------end
        text=get_ptext(paragr)
        if text == '' or text == '':
            continue
        if paraNum in part.keys():
            cur_part = part[paraNum]
        if cur_part == 'cover':
            if '��ҵ���'in text:
                cur_state = locate[paraNum] = 'cover2'
            elif  cur_state == 'cover2':
                cur_state = locate[paraNum] = 'cover3'
                title = text
                #print title
            elif 'Ժ'in text and'ϵ'in text or '����'in text:
                cur_state = locate[paraNum] = 'cover4'
            elif '��'in text and '��'in text:
                cur_state = locate[paraNum] = 'cover5'
        elif cur_part == 'spine':
            if '���ķ����鼹' in text:
                cur_state = locate[paraNum] = 'cover6'
            else:
                cur_state = locate[paraNum] = 'spine1'#���ô�����
        elif cur_part == 'statement':
            if text == '��������':
                cur_state = locate[paraNum] = 'statm1'
            elif text.startswith('������'):
                cur_state = locate[paraNum] = 'statm2'
            elif '����'in text:
                cur_state = locate[paraNum] = 'statm3'
            elif 'ʱ��' in text and  '��'in text  and '��' in text:
                last_text = text
            elif 'ʱ��'in last_text and  '��' in last_text and '��' in last_text and title in text:
                last_text = ''
                cur_state = locate[paraNum] = 'abstr1'
                
            elif 'ѧ'and'��'in text:
                cur_state = locate[paraNum] = 'abstr2'
        elif cur_part == 'abstract':
            if re.match(r'ժ *Ҫ',text):
                cur_state = locate[paraNum] = 'abstr3'
                last_text = text
            elif re.match(r'ժ *Ҫ',last_text):
                last_text = ''
                cur_state = locate[paraNum] = 'abstr4'
            elif '�ؼ���'in text or '�ؼ���'in text:
                cur_state = locate[paraNum] = 'abstr5'
                last_text = text
            elif cur_state == 'abstr5':
                last_text = ''
                cur_state = locate[paraNum] = 'abstr1'
            elif 'Author' in text:
                cur_state = locate[paraNum] = 'abstr2'
        elif cur_part == 'abstract_en':
            if text == 'ABSTRACT':
                cur_state = locate[paraNum] = 'abstr3'
                last_text = text
            elif last_text == 'ABSTRACT' and 'Author'not in text and 'Tutor'not in text:
                cur_state = locate[paraNum] = 'abstr4'
                last_text = ''
            elif ('KEY'in text or 'key' in text and 'WORD'in text or'word' in text )\
                 or ('keyword'in text or 'Keyword'in text or'KEYWORD'in text): 
                cur_state = locate[paraNum] = 'abstr5'
        elif cur_part == 'menu':
            if re.match(r'Ŀ *¼',text)or re.compile(r'ͼĿ¼').match(text) or re.compile(r'��Ŀ¼').match(text) or re.compile(r'ͼ��Ŀ¼').match(text):
                cur_state = locate[paraNum] = 'menuTitle'
                cur_state = locate[paraNum] ='menuFirst'
            elif analyse(text) == 'secondLv':
                cur_state = locate[paraNum] = 'menuSecond'
            elif analyse(text) == 'thirdLv':
                cur_state = locate[paraNum] = 'menuThird'
            else :
                cur_state = locate[paraNum] ='menuFirst'#�Ժ��ֿ�ͷ�ı��ⶼ��Ϊ��һ������
            if locate[paraNum] != 'menuTitle' and not text[-1].isdigit():
                cur_state = part[paraNum] = 'body'
                cur_part = 'body'
        elif cur_part == 'body':
            #�õ������Ȱ������ߣ��������Ϊ��ͨ���������ߡ�
            #print paraNum
            level = get_level(paragr)
            analyse_result = analyse(text)
            if analyse_result in['firstLv_e','secondLv_e','thirdLv_e']:
                warnInfo.append('    warning: ��������Ҫ�ͱ���֮���ÿո����')
                spaceNeeded.append(paraNum)
        #-------follow----hsy--modifies on July.13.2016
            if analyse_result is 'objectT':
                if cur_state != 'object':
                    #print 'warning',text
                    warnInfo.append('   warning: ͼ����ǰû��ֱ�Ӷ�Ӧ��ͼ')
            if cur_state is 'object':
                if analyse_result != 'objectT':
                    #print 'warning',text
                    warnInfo.append('   warning: ͼ��û�ж�Ӧ��ͼע��')
        #------end---------------------
            if level == '0':
                cur_state = locate[paraNum] = 'firstTitle'
                if analyse_result != 'firstLv' or analyse_result != 'firstLv_e':
                    #print 'warning',text
                    warnInfo.append('    warning: ���⼶��ͱ����Ŵ���ļ���һ��')
            elif level == '1':
                cur_state = locate[paraNum] = 'secondTitle'
                if analyse_result != 'secondLv' or analyse_result != 'secondLv_e':
                    #print 'warning',text
                    warnInfo.append('    warning: ���⼶��ͱ����Ŵ���ļ���һ��')
            elif level == '2':
                cur_state = locate[paraNum] = 'thirdTitle'
                if analyse_result != 'thirdLv' or analyse_result != 'thirdLv_e':
                    #print 'warning',text
                    warnInfo.append('    warning: ���⼶��ͱ����Ŵ���ļ���һ��')
            else:
                if analyse_result == 'firstLv':
                    cur_state = locate[paraNum] = 'firstTitle'
                elif analyse_result == 'secondLv' or analyse_result == 'secondLv_e':
                    cur_state = locate[paraNum] = 'secondTitle'
                elif analyse_result == 'thirdLv'or analyse_result == 'thirdLv_e':
                    cur_state = locate[paraNum] = 'thirdTitle'
                elif analyse_result == 'objectT':
                    cur_state = locate[paraNum] = 'objectTitle'
                elif analyse_result == 'tableT':
                    cur_state = locate[paraNum] = 'tableTitle'
                elif re.match(r'�� *��',text):
                    cur_state = locate[paraNum] = 'firstTitle'
                elif re.match(r'�� *л',text):
                    cur_state = locate[paraNum] = 'firstTitle'
                elif paragr.getparent().tag != '%s%s'% (word_schema,'body'): #��paragr�ĸ��ڵ㲻��bodyʱ����para���ı����������ģ������Ǳ��ͼ�λ��ı����ڵ�����
                    cur_state = locate[paraNum] = 'tableText'
                else:
                    cur_state = locate[paraNum] = 'body'
        elif cur_part == 'refer':
            if text == '�ο�����':
                cur_state = locate[paraNum] = 'firstTitle'
            else :
                cur_state = locate[paraNum] = 'reference'
                if not re.match('\\[[0-9]+\\]',text):
                    warnInfo.append('    warning: �ο����ױ�����[num]��ſ�ͷ��')
                
        elif cur_part == 'appendix':
            if text.startswith('��') and text.endswith('¼'):
                cur_state = locate[paraNum] = 'firstTitle'
            else:
                cur_state = locate[paraNum] = 'body'
##        if paraNum in locate.keys():
##            print locate[paraNum],text[0:(100 if len(text) > 100 else len(text))]
##        else:
##            print '\t\t',text
    for val in mentioned:
        if val in reference:
            reference.remove(val)
    return warnInfo


#���б��ı���ʲô��ͷ�ķ�����ʹ����������ʽ
def analyse(text):
    text=text.strip(' ')
    if text.isdigit():
        return 'body'
    pat1 = re.compile('[0-9]+')#�����ֿ�ͷ��������ʽ
    pat2 = re.compile('[0-9]+\\.[0-9]')#��X.X��ͷ��������ʽ
    pat3 = re.compile('[0-9]+\\.[0-9]\\.[0-9]')#��X.X.X��ͷ��������ʽ
    pat4 = re.compile('ͼ(\s)*[0-9]+(\\.|-)[0-9]')#ͼ�����������ʽ
    pat5 = re.compile('��(\s)*[0-9]+(\\.|-)[0-9]')#������������ʽ

#20160107 zqd -----------------------------------------------------------------------
    if pat1.match(text) and len(text)<70:
        if  pat1.sub('',text)[0] == ' ':
            sort = 'firstLv'
            #print 'the first LV length is',len(text)
        elif  pat1.sub('',text)[0] =='.':
            if pat2.match(text):
                if pat2.sub('',text)[0] == ' ':
                    sort = 'secondLv'
                elif pat2.sub('',text)[0]=='.':
                    if pat3.match(text):
                        if pat3.sub('',text)[0]==' ':
                            sort = 'thirdLv'
                        elif pat3.sub('',text)[0]=='.':
                            sort = 'overflow'
                            #print '    warning: ����������ļ����⣡'
                        else:
                            sort ='thirdLv_e'
                    else:
                        sort='secondLv_e2'
                        #print '    warning: ����������ȷ�ı�Ÿ�ʽΪX.X��'
                else:
                    sort = 'secondLv_e'
            else:
                sort = 'body'
        else:
            sort = 'firstLv_e'
    elif pat4.match(text) and len(text)<125:
        sort = 'objectT'
    elif pat5.match(text) and len(text)<125:
        sort = 'tableT'
    else :
        sort ='body'
#  zqd--------------------------------------------------------------------------------
    return sort

#��ȡ����ӿ�
def read_rules(filename):
    f=open(filename,'r')
    #���ֵ���Ҫ��������ǰ�˽ӿڶ��岻һ��Ϊ�˱����Ƭ�޸Ĵ���������(�Ѹ���һ��
    keyNameDc={'����_��λ����':'cover1',
               '����_��ҵ���':'cover2',
               '����_���ı���':'cover3',
               '����_������Ϣ':'cover4',
               '����_����':'cover5',
               '����_�鼹':'cover6',
               '��������_����':'statm1',
               '��������_����':'statm2',
               '��������_ǩ��':'statm3',
               'ժҪ_������Ŀ':'abstr1',
               'ժҪ_ѧ������ʦ����':'abstr2',
               'ժҪ_����':'abstr3',
               'ժҪ_����':'abstr4',
               'ժҪ_�ؼ���':'abstr5',
               'ժҪ_�ؼ�������':'abstr6',
               'Ŀ¼_����':'menuTitle',
               'Ŀ¼_һ������':'menuFirst',
               'Ŀ¼_��������':'menuSecond',
               'Ŀ¼_��������':'menuThird',
               '����_һ������':'firstTitle',
               '����_��������':'secondTitle',
               '����_��������':'thirdTitle',
               '����_����':'body',
               '��л_����':'unknown',#
               '��л_����':'unknown',#
               '��¼_����':'extentTitle',
               '��¼_����':'extentContent',
               'ͼ����':'objectTitle',
               '�����':'tableTitle',
               '�ο�����_��Ŀ':'reference'
               }
    
    rules_dct={}        
    for line in f:
        if line.startswith('{'):
            group=line[1:-3].split(',')
            for factor in group:
                _key = factor[:factor.index(':')]
                _val = factor[factor.index(':')+1:]
                if _key == 'key':
                    rule_dkey = _val
                    rules_dct.setdefault(_val,{})
                if _key!= 'key':
                    rules_dct[rule_dkey].setdefault(_key,_val)
    f.close()
    return rules_dct

#����ʽ��������
def check_out(rule,to_check,locate,paraNum):
    errorInfo=[]
    #����ֵ�Ķ�����Ҫ������ǰ̨�Ǹ�ͬѧ�����ֶκʹ��������ֶε����Ʋ�һ�£���
    errorTypeName={'fontCN':'font',
                   'fontEN':'font',
                   'fontSize':'fontsize',
                   'fontShape':'fontshape',
                   'paraAlign':'gradeAlign',
                   
                   'paraSpace':'gradeSpace',
                   'paraFrontSpace':'gradeFrontSpace',
                   'paraAfterSpace':'gradeAfterSpace',
                   'paraIsIntent':'FLind'
                   }
    errorTypeDescrip={'fontCN':'��������',
                   'fontEN':'Ӣ������',
                   'fontSize':'�ֺ�',
                   'fontShape':'����',
                   'paraAlign':'���뷽ʽ',
                   
                   'paraSpace':'�м��',
                   'paraFrontSpace':'��ǰ���',
                   'paraAfterSpace':'�κ���',
                   'paraIsIntent':'��������'
                      }
    
    #����ֵ�Ķ�����Ϊ�˱����ÿ��para���ѹ����ֵ���ʮ���ֶμ��һ�飬����para��λ����ѡ��������Եļ��
    checkItemDct={'cover1':['fontCN','fontSize'],
                  'cover2':['fontCN','fontSize','paraAlign'],
                  'cover3':['fontCN','fontSize','paraAlign'],
                  'cover4':['fontCN','fontSize','paraAlign'],
                  'cover5':['fontCN','fontSize','paraAlign'],
                  'cover6':[],
                  'statm1':['fontCN','fontSize','paraAlign','fontShape'],
                  'statm2':['fontCN','fontSize','paraAlign','paraSpace','paraIsIntent'],
                  'statm3':['fontCN','fontSize'],
                  'abstr1':['fontCN','fontSize','paraAlign','fontEN','paraIsIntent'],
                  'abstr2':['fontCN','fontSize','fontEN'],
                  'abstr3':['fontCN','fontSize','paraAlign','fontEN','paraIsIntent'],
                  'abstr4':['fontCN','fontSize','paraAlign','paraSpace','paraIsIntent','fontEN'],
                  'abstr5':['fontCN','fontSize','paraAlign','fontShape','fontEN'],
                  'abstr6':['fontCN','fontSize','fontEN'],
                  'menuTitle':['fontCN','fontSize','paraAlign','paraSpace','fontShape','paraFrontSpace','paraAfterSpace','paraIsIntent'],
                  'menuFirst':['fontCN','fontSize'],
                  'menuSecond':['fontCN','fontSize'],
                  'menuThird':['fontCN','fontSize'],
                  'firstTitle':['fontCN','fontSize','paraAlign','paraSpace','fontShape','paraFrontSpace','paraAfterSpace','paraIsIntent'],
                  'secondTitle':['fontCN','fontSize','paraAlign','paraSpace','fontShape','paraFrontSpace','paraAfterSpace','paraIsIntent'],
                  'thirdTitle':['fontCN','fontSize','paraAlign','paraSpace','fontShape','paraFrontSpace','paraAfterSpace','paraIsIntent'],
                  'body':['fontCN','fontEN','fontSize','fontShape','paraIsIntent'],
                  'tableText':['fontCN','fontEN','fontSize','fontShape'],
                  'thankTitle':['fontCN','fontSize'],
                  'thankContent':['fontCN','fontEN','fontSize'],
                  'extentTitle':['fontCN','fontSize'],
                  'extentContent':['fontCN','fontEN','fontSize'],
                  'objectTitle':['fontCN','fontSize'],
                  'tableTitle':['fontCN','fontSize'],
                  'reference':['fontCN','fontEN','fontSize','paraAlign','fontShape','paraIsIntent']
                  }
    if locate in checkItemDct.keys():
        for key in checkItemDct[locate]:
            if key == 'paraIsIntent':#�����������ر���
                #print '00000000000000000',to_check['paraIsIntent1'],to_check['paraIsIntent']
                if to_check['paraIsIntent1'] != 'δ��ȡ����ֵ' and to_check['paraIsIntent1'] != '0':
                    if to_check['paraIsIntent1'] != '200' and rule['paraIsIntent'] == '1':
                        rp1.write(str(paraNum)+'_'+locate+'_'+'error_paraIsIntent1_200\n')
                    elif rule['paraIsIntent'] == '0':
                        rp1.write(str(paraNum)+'_'+locate+'_'+'error_paraIsIntent1_0\n')
                else:
                    #if to_check['paraIsIntent'] != str(int(rule['paraIsIntent'])*int(rule[key])*20):
                    if int(to_check['paraIsIntent']) < 100:#������һ�����Ե��趨����ΪҪ�ǰ�������ע�͵�һ����ִ�У�������̫����
                        rp1.write(str(paraNum)+'_'+locate+'_'+'error_paraIsIntent_'+str(20*int(to_check['fontSize'])*int(rule[key]))+'\n')
                continue
            else:
                if to_check[key] != rule[key]:
                    #print '    ��ʽ��',key,to_check[key]
                    rp.write('    '+errorTypeDescrip[key]+'��'+to_check[key]+'  ��ȷӦΪ��'+rule[key]+'-------->'+ptext+'\n')
                    errorInfo.append('\'type\':\''+errorTypeName[key]+'\',\'correct\':\''+rule[key]+'\'')
                    rp1.write(str(paraNum)+'_'+locate+'_error_'+key+'_'+rule[key]+'\n')
                    #if key == 'fontSize':
                        #print '---------',to_check[key],rule[key]
##    else:
##        for key in errorTypeName:
##            if to_check[key] != rule[key]:
##                #print '    ��ʽ��',key,to_check[key]
##                #Ϊ����ǰ̨�Ǹ�ͬѧ��JS��ʽ��Ҫ��ÿ������ֵ�������˵�����
##                errorInfo.append('\'type\':\''+errorTypeName[key]+'\',\'correct\':\''+rule[key]+'\'')

    return errorInfo

def grade2num():
    # 20160121 zqd
    # modified: xml_tree
    numPrIlvl = [0,0,0,0]
    for paragr in _iter(xml_tree,'p'):
        for pPr in paragr.iter(tag=etree.Element):
            if _check_element_is(pPr,'pPr'):
                for numPr in pPr.iter(tag=etree.Element):
                    if _check_element_is(numPr,'numPr'):
                        for ilvl in numPr.iter(tag=etree.Element):
                            if _check_element_is(ilvl,'ilvl'):
                                if has_key(ilvl,'val'):#�д�����
                                    
                                    result = get_val(ilvl,'val')
                                    if result == "0":
                                        numPrIlvl[0] += 1
                                        numPrIlvl[1] = numPrIlvl[2] = numPrIlvl[3] = 0
                                    elif result == "1":
                                        numPrIlvl[1] += 1
                                        numPrIlvl[2] = numPrIlvl[3] = 0
                                    elif result == "2":
                                        numPrIlvl[2] += 1
                                        numPrIlvl[3] = 0
                                    elif result == "3":
                                        numPrIlvl[3] += 1
                                    strNumPr = ""
                                    i = 0
                                    while numPrIlvl[i] != 0 and i < 4:
                                        strNumPr += str(numPrIlvl[i])+"."
                                        i+=1
                                    pPr.remove(numPr)
                                    for node in paragr.iter(tag=etree.Element):
                                        if _check_element_is(node,'t'):
                                            node.text = strNumPr+" "+node.text
                                            break
                                    #print etree.tostring(paragr,encoding="UTF-8",pretty_print=True)


        
startTime=time.time()  
#������__main__��ڲ����������
xml_from_file,style_from_file = get_word_xml(Docx_Filename)
xml_tree   = get_xml_tree(xml_from_file)
style_tree = get_xml_tree(style_from_file)

rules_dct=read_rules(Rule_Filename)#���������ȡ����ֻ������һ�Σ�д�ɺ���Ҳ������


Part='start'
previousL='unknown'
part = {}
locate = {}
paraNum=0
reference = []
spaceNeeded = []
empty_para=0
#sys.exit()
reference = first_locate()
warninglist = second_locate()
#print locate
#sys.exit()
Report='['
Report1 = '['
rp = open(Out_DirPath + 'check_out.txt','w')
rp1 = open(Out_DirPath + 'check_out1.txt','w')
rp2 = open(Out_DirPath + 'space.txt','w')
eInfo = ''
section_seq = 0
rp.write('''���ĸ�ʽ��鱨���ĵ�ʹ��˵����
*****�˰汾Ϊ�������߲��԰棬����������е�������⣬��������ʱ���½⣬�����Խ����ⷴ�����������Ƴ����_��*****
���ֶ�ֵ˵����
λ��  Ϊ�����жϸö����ı����������п��ܵ�λ�ã�������������������λ�ò�������������ĸ�ʽ�����Ϣ
����  0��ʾδ�Ӵ֣�1��ʾ�Ӵ�
�м�� N=��ֵ/240����ΪN���о�
��ǰ�κ����ֵ��λ��Ϊ��
��������0��ʾ����δ������1��ʾ��������2�ַ�
warning��Ϣ��ʾ���ܴ��ڵ����⣬��һ��׼ȷ
**********���������ķָ��ߣ�Ȼ���ѣ�**********


''')
graphTitlePattern = re.compile('ͼ(\s)*[0-9]+(\\.|-)[0-9]')#ͼ�����������ʽ
wrongGraphTitlePattern = re.compile('ͼ(\s)*[0-9]')#����ͼ�����������ʽ
excelTitlePattern = re.compile('��(\s)*[0-9]+(\\.|-)[0-9]')#ͼ�����������ʽ
wrongExcelTitlePattern = re.compile('��(\s)*[0-9]')#����ͼ�����������ʽ
ObjectFlag=0
p_format={}.fromkeys(['fontCN','fontEN','fontSize','paraAlign','fontShape','paraSpace',
                         'paraIsIntent','paraFrontSpace','paraAfterSpace','paraGrade'])
for paragr in _iter(xml_tree,'p'):
#��<w:p>Ϊ��С��λ����

    paraNum +=1
    ptext=get_ptext(paragr)
    if ObjectFlag == 1:
        if not graphTitlePattern.match(ptext):
            rp.write('     warning: �Ҳ�����Ӧͼע ----->'+ptext+'\n')
        ObjectFlag = 0
    if graphTitlePattern.match(ptext):
        if paraNum - 1 in locate.keys():
            if locate[paraNum - 1] != 'object':
                rp.write('    warning: û�ж�Ӧ��ͼ��--->' + ptext + '\n')
        else:
            rp.write('    warning: û�ж�Ӧ��ͼ��--->' + ptext + '\n')
        found = False
        for node in paragr.iter(tag=etree.Element):
            if _check_element_is(node, 'r'):
                for bookmarks in node.iter(tag=etree.Element):
                    if _check_element_is(bookmarks, 'bookmarkStart'):
                        if bookmarks.values()[1][:4] == '_Ref':
                            found = True
        if not found:
            rp.write('    ��ͼעû�����ù�' + ptext + '\n')
    if wrongGraphTitlePattern.match(ptext) and not graphTitlePattern.match(ptext):
        rp.write('    warning: ���Ϊ���Ϲ����ͼע ------>' + ptext + '\n')
        found = False
        for node in paragr.iter(tag=etree.Element):
            if _check_element_is(node, 'r'):
                for bookmarks in node.iter(tag=etree.Element):
                    if _check_element_is(bookmarks, 'bookmarkStart'):
                        if bookmarks.values()[1][:4] == '_Ref':
                            found = True
        if not found:
            rp.write('    ��ͼעû�����ù�' + ptext + '\n')
    if excelTitlePattern.match(ptext):
        found = False
        for node in paragr.iter(tag = etree.Element):
            if _check_element_is(node, 'r'):
                for bookmarks in node.iter(tag = etree.Element):
                    if _check_element_is(bookmarks, 'bookmarkStart'):
                        if bookmarks.values()[1][:4] == '_Ref':
                            found = True
        if not found:
            rp.write('    ��ͼעû�����ù�' + ptext + '\n')
    if wrongExcelTitlePattern.match(ptext) and not excelTitlePattern.match(ptext):
        rp.write('    warning: ���Ϊ���Ϲ����ͼע------->'+ptext+'\n')
        found = False
        for node in paragr.iter(tag=etree.Element):
            if _check_element_is(node, 'r'):
                for bookmarks in node.iter(tag=etree.Element):
                    if _check_element_is(bookmarks, 'bookmarkStart'):
                        if bookmarks.values()[1][:4] == '_Ref':
                            found = True
        if not found:
            rp.write('    warning: ��ͼעû�����ù�' + ptext + '\n' )
    if paraNum in locate.keys():
        location = locate[paraNum]
        if location == 'object':
            ObjectFlag = 1
    if  ptext == ' ' or ptext == '':
        empty_para += 1
        warnInfo=[]
        if empty_para==2:
            #print paraNum,' '
            record='{\'paraNum\':\''+str(paraNum)+'\',\'Level\':\'warning\',\'type\':\'warn\',\'correct\':\'    warning:����������������У�\'},'
            Report += record
            rp.write('     warning:����������������� \n')
            #print '    warning:����������������У�'
        continue
    empty_para =0
    get_format(paragr,p_format)
    #print paraNum,ptext
    #rp.write(str(paraNum)+' '+ptext+'\n')


    first_text = 0
    for run in _iter(paragr,'r'):
        flag = 0
        for w_t in _iter(run,'t'):
            if w_t.text != None and w_t.text != ' ':
                flag = 1

        if flag == 0:
                 continue
        for rPr in _iter(run,'rPr'):
            if first_text == 0:
                assign_fd(rPr,p_format)
                first_text = 1
            else:
                for detail in rPr.iter(tag=etree.Element):
                    if _check_element_is(detail,'rFonts'):
                        if has_key(detail,'eastAsia'):#�д�����
                            if p_format['fontCN'] != get_val(detail,'eastAsia').encode(Unicode_bt):
                                rp1.write(str(paraNum)+'_'+location+'_error_fontCN_'+rules_dct[location]['fontCN']+'\n')
                                break
                    elif _check_element_is(detail,'sz'):
                        if p_format['fontSize'] != get_val(detail,'val'):
                            rp1.write(str(paraNum)+'_'+location+'_error_fontSize_'+rules_dct[location]['fontSize']+'\n')
                            break
            
    


##        if warnInfo:
##            for each in warnInfo:
##                rp.write(each+'\n')
##                record='{\'paraNum\':\''+str(paraNum)+'\',\'Level\':\'warning\',\'type\':\'warn\',\'correct\':\''+each+'\'},'
##                

    #�ؼ�������Ƚ����⣬Ҫ����para�ڲ�����run��rpr�����ؼ������ݵĸ�ʽ
    if location=='abstr5':
        if ':' not in ptext and '��' not in ptext :
            record='{\'paraNum\':\''+str(paraNum)+'\',\'Level\':\'warning\',\'type\':\'warn\',\'correct\':\'    warning: �ؼ��ʺ���û��ð�ţ�\'},'
            rp.write('    warning: �ؼ��ʺ���û��ð�ţ�------>'+ptext+'\n')
            Report += record
            
            
        for rpr_keyword in _iter(paragr,'rPr'):
            found=0
            for bold_sign in _iter(rpr_keyword,'b'):
                found=1
        if not found:
            record='{\'paraNum\':\''+str(paraNum)+'\',\'Level\':\'warning\',\'type\':\'warn\',\'correct\':\'    warning: �ؼ�������û�мӴ֣�\'},'
            Report += record
            rp.write('    warning: �ؼ�������û�мӴ֣�'+ptext+'\n')

    #ͼ/�� ������Ҫ����Ƿ�ʹ�������ã��Լ�ͼ/�� ����Ƿ���½ڱ��һ��, �ⲿ��û�аѴ�����Ϣ���뵽checkout1.txt��modify.pyҲ��û��д�޸��ºŵķ���
    if location in[ 'firstTitle','secondTitle','thirdTitle']:
        ptext.strip(' ')#ɾ����ͷ�Ŀո��ַ�
        if ptext[0].isdigit():
            section_seq = int(ptext[0])
        else:
            section_seq=0
    elif location in ['objectTitle','tableTitle']:
        pat7 = re.compile('(ͼ|��)(\s)*')
        if pat7.sub('',ptext)[0].isdigit():
            testtext = pat7.sub('',ptext)[0]
            if section_seq != int(pat7.sub('',ptext)[0]):
                record='{\'paraNum\':\''+str(paraNum)+'\',\'Level\':\'warning\',\'type\':\'warn\',\'correct\':\'    warning: ͼ/�� ������½ڱ�Ų�һ�� ���½�һ�������ʽ����ȷ���³���δʶ�������\'},'
                Report += record
                rp.write('    waring:ͼ�� ��ź��½ڲ�һ��------->'+ptext+'\n')
        found=0
        for refer in _iter(paragr,'fldChar'):
            found=1
        if not found:
            record='{\'paraNum\':\''+str(paraNum)+'\',\'Level\':\'warning\',\'type\':\'warn\',\'correct\':\'    warning: ͼ/�� ����δʹ�����ã�\'},'
            Report += record
            #print '    warning: ͼ/�� ����δʹ�����ã�'
            rp.write('    warning: ͼ/�� ���� δʹ�ø���ͼ������-------->'+ptext+'\n')

    #�������������˲ο����׵�ʱ�򣬱��Ҫʹ���ϱ��ʽ���������⣺���Ի��һ��������������г� �ο����׵ı�ţ��ⲿ��û�аѴ�����Ϣ���뵽checkout1.txt��modify.pyҲ��û��д�޸��ºŵķ���
    if location =='reference':
        pat6 = re.compile('\\[[0-9]+\\]')#�ο����ױ�ŵ�������ʽ
        if pat6.search(ptext):
            used_superscript=0
            for run in _iter(paragr,'r'):
                rtext=get_ptext(run)
                if pat6.match(rtext):
                    for superscript in _iter(run,'vertAlign'):
                        if has_key(superscript,'val'):
                            used_superscript=1
            if not used_superscript:
                record='{\'paraNum\':\''+str(paraNum)+'\',\'Level\':\'warning\',\'type\':\'warn\',\'correct\':\'    warning: �����вο����׵�����δʹ���ϱ꣡\'},'
                Report += record
                rp.write('    warning: �����вο����׵�����δʹ���ϱ꣡------>'+ ptext+'\n')
                            
    
    if location in rules_dct.keys():
        #rp.write('    λ�ã�'+rules_dct[location]['name']+'\n')
        #print '    λ�ã�',rules_dct[location]['name']
        errorInfo=check_out(rules_dct[location],p_format,location,paraNum)
    else:
        #print '��λʧ�ܣ�����ӿ���δ����ö������'
        #print location
        errorInfo=''
    if errorInfo :
        #print '    ��飺 False'
        for each in errorInfo:
            #print '    ӦΪ��',each
            record='{\'paraNum\':\''+str(paraNum)+'\',\'Level\':\'error\','+each+'},'
            Report += record
    else:
        pass
        #rp.write('    ��飺 ��ʽ��ȷ\n')
        #print '    ��飺 True'
for num in spaceNeeded:
    rp2.write('%d' %num)
    rp2.write('\n')
        

Report += ']'
#print Report



endTime=time.time()
print '   ��ʱ�� %.2f ms' % (100*(endTime-startTime))


hyperlinks = []
bookmarks = []
#���Ŀ¼�Ƿ��Զ�����
for node in _iter(xml_tree, 'hyperlink'):
    temp=''
    for hl in _iter(node,'t'):
        temp += hl.text
    hyperlinks.append(node.values()[0])
    #print True,temp
for node in _iter(xml_tree, 'bookmarkStart'):
    bookmarks.append(node.values()[1])

catalog_ud= True
for i in hyperlinks:  
    if i not in bookmarks:
        catalog_ud =False
if catalog_ud:
    pass
    #print True,'Ŀ¼��������'
else:
    pass
    #print False,'Ŀ¼δ����'

#rp.write('\n\n\n���ĸ�ʽ�����ϣ�\n')
#rp.write(Report)
rp.close()
rp1.close()
rp2.close()
###---zqd ���� 20160121-------------------------------------------------
##zipF = zipfile.ZipFile(Docx_Filename)
###������ʱĿ¼
##tmp_dir = tempfile.mkdtemp()
###��ԭ����docx��ѹ����ʱĿ¼
##zipF.extractall(tmp_dir)
###���µ�xmlд������
##with open(os.path.join(tmp_dir,'word/document.xml'),'w') as f:
##    xmlstr = etree.tostring (xml_tree, pretty_print=True,encoding="UTF-8")#�˴���ʶ��'gb2312'
##    f.write(xmlstr)
##
### Get a list of all the files in the original docx zipfile
##filenames = zipF.namelist()
### Now, create the new zip file and add all the filex into the archive
##zip_copy_filename = 'result.docx'
##with zipfile.ZipFile(zip_copy_filename, "w") as docx:
##    for filename in filenames:
##        docx.write(os.path.join(tmp_dir,filename),  filename)
##
### Clean up the temp dir
##shutil.rmtree(tmp_dir)
###-----------------------------------------------             
    
