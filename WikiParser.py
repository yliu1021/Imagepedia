import wikipedia

class Section:

    def __init__(self, text, indLvl = 1):
        self.indentationLevel = indLvl
        self.content = ''
        self.subsections = []
        
        lines = [x for x in text.split('\n') if x != '']

        title = lines[0]
        while title.startswith('='):
            title = title[1:]
        title = title[1:]
        while title.endswith('='):
            title = title[:-1]
        title = title[:-1]
        if title.endswith("Edit"):
            title = title[:-4]
        self.title = title
        lines = lines[1:]
        for i in range(len(lines)):
            hLevel = self.isHeader(lines[i])
            if hLevel == -1:
                self.content += lines[i] + '\n'
            else:
                lines = lines[i:]
                break
        else:
            return

        subsectionLines = []
        for line in lines:
            iLvl = self.isHeader(line)
            if iLvl == self.indentationLevel + 1:
                if len(subsectionLines) == 0:
                    subsectionLines.append(line)
                    continue
                self.subsections.append(Section('\n'.join(subsectionLines), iLvl))
                subsectionLines = [line]
            else:
                subsectionLines.append(line)
        if len(subsectionLines) != 0:
            self.subsections.append(Section('\n'.join(subsectionLines), self.indentationLevel + 1))

    def isHeader(self, s):
        if s.startswith('='):
            return s.find(" ")
        else:
            return -1

    def __str__(self):
        ind = self.indentationLevel - 1
        indC = "\t"
        i = ind * indC
        title = i + "Title: " + self.title + "\n"
        content = i + "Content: " + self.content + "\n" if len(self.content) != 0 else ""
        s = title + content

        acc = ""
        for section in self.subsections:
            acc += repr(section)
        s += acc

        return s.encode("ascii") + '\n'


    def __repr__(self):
        try:
            return self.__str__()
        except TypeError:
            return "empty"
        except UnicodeEncodeError:
            return "unicode error"


def createSection(topic):
    url = None
    try:
        page = wikipedia.page(topic)
        c = page.content
        url = page.url
        c = "= " + page.title + " =\n" + c
    except wikipedia.exceptions.PageError:
        return None
    except wikipedia.exceptions.DisambiguationError:
        return None
    
    x = Section(c)
    x.url = url
    return x
