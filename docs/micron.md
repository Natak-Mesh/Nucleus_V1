Title: Markup
Date: 2023-05-16

# Outputting Formatted Text

---

**Hello!** This is output from *micron*
Micron generates formatted text for your terminal

---

Nomad Network supports a simple and functional markup language called *micron*. If you are familiar with *markdown* or *HTML*, you will feel right at home writing pages with micron.

With micron you can easily create structured documents and pages with formatting, colors, glyphs and icons, ideal for display in terminals.

##Recommendations and Requirements

While micron can output formatted text to even the most basic terminal, there's a few capabilities your terminal *must* support to display micron output correctly, and some that, while not strictly necessary, make the experience a lot better.

Formatting such as _underline_, **bold** or *italics* will be displayed if your terminal supports it.

If you are having trouble getting micron output to display correctly, try using *gnome-terminal* or *alacritty*, which should work with all formatting options out of the box. Most other terminals will work fine as well, but you might have to change some settings to get certain formatting to display correctly.

###Encoding

All micron sources are intepreted as UTF-8, and micron assumes it can output UTF-8 characters to the terminal. If your terminal does not support UTF-8, output will be faulty.

###Colors

Shading and coloring text and backgrounds is integral to micron output, and while micron will attempt to gracefully degrade output even to 1-bit terminals, you will get the best output with terminals supporting at least 256 colors. True-color support is recommended.

###Terminal Font

While any unicode capable font can be used with micron, it's highly recommended to use a *"Nerd Font"* (see https://www.nerdfonts.com/), which will add a lot of extra glyphs and icons to your output.

If you want to make a break, horizontal dividers can be inserted. They can be plain, like the one below this text, or you can style them with unicode characters and glyphs, like the wavy divider in the beginning of this document.

-

Text can be _underlined_, **bold** or *italic*.

###Sections and Headings

You can define an arbitrary number of sections and sub sections, each with their own named headings. Text inside sections will be automatically indented.

-

If you place a divider inside a section, it will adhere to the section indents.

#####

If no heading text is defined, the section will appear as a sub-section without a header. This can be useful for creating indented blocks of text, like this one.

# Micron tags

Tags are used to format text with micron. Some tags can appear anywhere in text, and some must appear at the beginning of a line. If you need to write text that contains a sequence that would be interpreted as a tag, you can escape it with the character \\.

##Formatting

Text can be formatted as **bold** by using the `**` tag, _underline_ by using the `_` tag and *italic* by using the `*` tag.

##Sections

To create sections and subsections, use the # tag. This tag must be placed at the beginning of a line. To specify a sub-section of any level, use any number of # tags. If text is placed after a # tag, it will be used as a heading.

Here is an example of sections:

```
# High Level Stuff
This is a section. It contains this text.

## Another Level
This is a sub section.

### Going deeper
A sub sub section. We could continue, but you get the point.

####
Wait! It's worth noting that we can also create sections without headings. They look like this.

```

The above markup produces the following output:

# High Level Stuff
This is a section. It contains this text.

## Another Level
This is a sub section.

### Going deeper
A sub sub section. We could continue, but you get the point.

> Wait! It's worth noting that we can also create sections without headings. They look like this.

#Links

Links to pages, files or other resources can be created with the `[` tag, which should always be terminated with a closing `]`. You can create links with and without labels, it is up to you to control the formatting of links with other tags. Although not strictly necessary, it is good practice to at least format links with underlining.

Here's a few examples:

```
Here is a link without any label: [72914442a3689add83a09a767963f57c:/page/index.mu]

This is a [labeled link](72914442a3689add83a09a767963f57c:/page/index.mu) to the same page, but it's hard to see if you don't know it
```

The above markup produces the following output:

Here is a link without any label: [72914442a3689add83a09a767963f57c:/page/index.mu]

This is a [labeled link](72914442a3689add83a09a767963f57c:/page/index.mu) to the same page, but it's hard to see if you don't know it

---

When links like these are displayed in the built-in browser, clicking on them or activating them using the keyboard will cause the browser to load the specified URL.

#Literals

To display literal content, for example source-code, or blocks of text that should not be interpreted by micron, you can use literal blocks, specified by the ``` tag.
