from bs4 import BeautifulSoup, Tag
import requests
from urllib.parse import urljoin
import os
import json

def get_data(product):
    urls = {'dishwasher': 'https://www.partselect.com/Dishwasher-Models.htm', 'refrigerator': 'https://www.partselect.com/Refrigerator-Models.htm'}
    product_url = urls[product]
    #get_product_links(urls[product])
    # part_url = 'https://www.partselect.com/PS10065979-Whirlpool-W10712395-Upper-Rack-Adjuster-Kit-White-Wheels-Left-and-Right-Sides.htm?SourceCode=18' # delete
    # part = get_part(part_url)
    # print('get part: ')
    # print(part)
    model_links = get_model_links(product_url)
    models = {}
    parts = {}

    # a dictionary of model number to model object
    for model_link in model_links:
        model = get_model(model_link, parts)
        model_number = model['model_number']
        model_name = model['model_name']
        model_identifier = model_number + ',' + model_name
        models[model_identifier] = model

    # print('parts length: ', len(parts))
    # print('parts: ', parts)
    # print('model length: ', len(models))
    # print('models: ', models)

def get_model_links(base_url):
    model_links = []
    page_num = 1
    # while True:
    while page_num == 1:
        url = f"{base_url}?start={page_num}"
        try:
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            ul_element = soup.find('ul', class_='nf__links')
            li_elements = ul_element.find_all('li')

            num = 1 #delete
            for li in li_elements:
                if num > 1: #delete
                    break
                a_tag = li.find('a')
                if a_tag:
                    # model_name = a_tag.text.strip()
                    href = a_tag['href']

                    full_url = f"https://www.partselect.com/{href}"
                    
                    model_links.append(full_url)
                num += 1 #delete

            # Check if there's a next page
            pager_container = soup.find('div', class_='pager-container')
            next_disabled = pager_container.find('li', class_='next disabled') if pager_container else None
            if not next_disabled:
                page_num += 1
            else:
                break

        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL: {url}")
            print(e)
            break
    return model_links

# returns a model object given the url and the parts dictionary
def get_model(url, parts):
    model = {}
    model['parts'] = []
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        title = soup.find('h1', class_='title-main mt-3 mb-4').text.strip()[:-11]
        space_index = title.index(' ')
        model_number = title[:space_index].strip()
        model_name = title[space_index+1:].strip()
        model['model_name'] = model_name
        model['model_number'] = model_number
        model_identifier = model_name + ',' + model_number

        parts_url = get_model_parts(url)
        for part_select, part_url in parts_url.items():
            model['parts'].append(part_select)
            if part_select not in parts:
                part = get_part(part_url)
                parts[part_select] = part

                #creating and writing to part files
                folder_path = '/Users/kzheng/Dropbox/Programming/Instalily/backend/venv/crawler/parts'
                file_name = part_select + '.txt'
                file_path = os.path.join(folder_path, file_name)
                with open(file_path, 'w') as file:
                    json.dump(part, file, indent=4)

            parts[part_select]['compatible_models'].append(model_identifier)

        model['section'] = get_model_section(soup)
        model['symptom'] = get_model_symptoms(soup)

        #creating and writing to model files
        folder_path = '/Users/kzheng/Dropbox/Programming/Instalily/backend/venv/crawler/models'
        file_name = model_identifier + '.txt'
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, 'w') as file:
            json.dump(model, file, indent=4)

        return model

    except requests.exceptions.RequestException as e:
            print(f"Error fetching URL: {url}")
            print(e)

    # print('model url: ', url)
    # print(parts)
    # print(len(parts))


# returns all parts of a model in a dictionary from part select to part url
def get_model_parts(model_url):
    base_url = model_url + 'Parts/'
    page_num = 1
    parts = {}
    while True:
        try: 
            model_parts_url = f'{base_url}?start={page_num}'
            response = requests.get(model_parts_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            part_list = soup.find('div', class_='row mt-3 align-items-stretch')
            parts_element = part_list.find_all('div', {'class': 'mega-m__part'})
            for part in parts_element:
                part_info = part.find('div', class_='d-flex flex-col justify-content-between')
                part_name_element = part_info.find('a', class_='bold mb-1 mega-m__part__name')
                href = part_name_element['href']
                part_url = f"https://www.partselect.com/{href}"
                part_select_div = None
                for child in part_info.find('div'):
                    if isinstance(child, Tag) and child.name == 'div':
                        part_select_div = child
                        break
                part_select_span = part_select_div.find('span')
                part_select = part_select_span.next_sibling.strip()
                parts[part_select] = part_url

            pager_container = soup.find('div', class_='pager-container')
            next_disabled = pager_container.find('li', class_='next disabled') if pager_container else None

            if not next_disabled:
                    page_num += 1
            else:
                break

        except requests.exceptions.RequestException as e:
                print(f"Error fetching URL: {url}")
                print(e)
    return parts

#this method takes in the url for the part and returns a part object
def get_part(part_url):
    try:
        response = requests.get(part_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        page_top = soup.find_all('div', {'class': 'col-lg-6'})[1]
        
        price = soup.find('span', class_='js-partPrice').text.strip()
        name = soup.find('h1', class_='title-lg mt-1 mb-3').text.strip()

        manufacture_elements = page_top.find_all('div', {'class': 'mb-2'})
        manufacture_number_div = manufacture_elements[-2]
        manufacturer_div = manufacture_elements[-1]
        manufacture_number = manufacture_number_div.find('span').text.strip()
        manufacturer = manufacturer_div.find('span').find('span').text.strip()

        description = ''
        description_div = soup.find('div', class_='pd__description pd__wrap mt-3')
        if description_div:
            description = description_div.find('div', class_='mt-3').text.strip()

        troubleshooting = {}
        troubleshooting_element = soup.find('div', class_='pd__wrap row')
        troubleshooting_rows = []
        if troubleshooting_element:
            troubleshooting_rows = troubleshooting_element.find_all('div', {'class': 'col-md-6 mt-3'})
        for row in troubleshooting_rows:
            title_div = row.find('div')
            title = title_div.text.strip()
            text = title_div.next_sibling.strip()
            if not text:
                text = row.find_all('div')[1].text.strip()
            troubleshooting[title] = str_to_list(text)

        # print('price: ', price)
        # print('name: ', name)
        # print('manufacture number: ', manufacture_number)
        # print('manufacturer: ', manufacturer)
        # print('description: ', description)
        # print('troubleshooting: ', troubleshooting)
        # print('compatible models: ', len(compatible_models))

        part = {
            'price': price,
            'name': name,
            'manufacture_num': manufacture_number,
            'manufacturer': manufacturer,
            'description': description,
            'troubleshooting': troubleshooting,
            'compatible_models': []
        }

        return part

    except requests.exceptions.RequestException as e:
                print(f"Error fetching URL: {url}")
                print(e)


def get_model_section(model_soup):
    section_container = model_soup.find('div', class_='row mb-3')
    section_elements = section_container.find_all('div', {'class': 'col-6 col-sm-4 col-md-3 col-lg-2'})
    sections = {}
    for section in section_elements:
        a_tag = section.find('a')
        full_url = ''
        if a_tag:
            href = a_tag['href']
            full_url = f"https://www.partselect.com{href}"
        name = section.find('span').text.strip()
        sections[name] = get_section_parts(full_url)
    return sections

def get_section_parts(section_url):
    parts = []
    try:
        response = requests.get(section_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        parts_element = soup.find_all('div', {'class': 'three-pane__model-display__parts-list__part-item js-ua-ms-partrow'})
        for part_div in parts_element: 
            a_tag = part_div.find('span').find('a')
            part_select = ''
            if a_tag:
                part_select = a_tag.text.strip()
                parts.append(part_select)
        return parts


    except requests.exceptions.RequestException as e:
                print(f"Error fetching URL: {url}")
                print(e)

def get_model_symptoms(model_soup):
    symptoms = {}
    symptom_elements = model_soup.find_all('a', {'class': 'symptoms'})
    for symptoms_tag in symptom_elements:
        description = symptoms_tag.find('div', class_='symptoms__descr')
        symptom_url = symptoms_tag['href']
        full_url = f'https://www.partselect.com{symptom_url}'
        if description:
            name = description.text.strip()
            symptoms[name] = get_symptom_parts(full_url)

    return symptoms

def get_symptom_parts(symptom_url):
    parts = []
    try:
        response = requests.get(symptom_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        parts_div = soup.find_all('div', {'class': 'symptoms align-items-center'})
        for part_div in parts_div:
            part_select = part_div.find('div', class_='text-sm mb-2 mb-sm-0').find('a').text.strip()
            parts.append(part_select)

        parts_div = soup.find_all('div', {'class': 'symptoms align-items-center d-none'})
        for part_div in parts_div:
            part_select = part_div.find('div', class_='text-sm mb-2 mb-sm-0').find('a').text.strip()
            parts.append(part_select)
        return parts

    except requests.exceptions.RequestException as e:
                print(f"Error fetching URL: {url}")
                print(e)

def str_to_list(text):
    if text[-1] == '.':
        text = text[:-1]
    arr = []
    if ',' in text:
        arr = text.split(',')
    elif '|' in text:
        arr = text.split('|')
    return [word.strip() for word in arr]