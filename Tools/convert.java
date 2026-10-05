import java.io.*;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Stack;

public class convert
{
    private int l = 1;
    private int p = 1;
    private byte sp = 32;
    private byte nl = 10;
    private byte tb = 9;
    private byte hyphen = 45;
    private byte dot = 46;
    private byte vert = 124;

    public static void main(String[] args) throws IOException
    {
        if (args.length <1) { System.out.println("No files to process!"); }
        else
        {
            for(String f : args)
                if (f.endsWith(".md"))
                    process(f);
                else
                    processMD(f);
        }
    }

    private static void process(String f) throws IOException
    {
        System.out.println("Process File: " + f);

        ArrayList<Byte> data = new ArrayList<Byte>();

        for(String s : Files.readAllLines(Paths.get(f), StandardCharsets.UTF_8))
        {
            Stack<Byte> S = new Stack<Byte>();

            for(int i = 0; i<s.length(); i++)
            {
                int k = (int) s.charAt(i);
                if (k==9)
                {
                    if (f.equals("Makefile")||f.endsWith(".sln")||
                        f.endsWith(".fsproj")||f.endsWith(".csproj"))
                        { p+=1; S.push(tb); }
                    else { p+=4; S.push(sp); S.push(sp); S.push(sp); S.push(sp); }
                }
                else if (k == 13) /* carriage return */  p++;
                else if ((k > 31) && (k<128)) { p++; S.push((byte) k); }
                else if (k == nl) { System.out.println("Illegal new line at line: " +
                                    l + " position: " + p); System.exit(1); }
                else if (k == 8211) { p++; S.push(hyphen); }
                else if (k == 8212) { p++; S.push(hyphen); }
                else if (k == 160) { p++; S.push(sp); }
                else if (k == 183) { p++; S.push(dot); }
                else if (k == 9472) { p++; S.push(hyphen); }
                else if (k == 9492) { p++; S.push(hyphen); }
                else
                {
                    System.out.println("Illegal char at line: " + l + " position: "
                                    + p + " with value " + s.charAt(i) + "(" + k + ")");
                    p++;
                }
            }

            while ( (!S.empty()) && (S.peek() == sp) ) S.pop();
            Stack<Byte> SS = new Stack<Byte>();
            while (!S.empty()) SS.push(S.pop());
            while (!SS.empty()) data.add(SS.pop());

            data.add(nl); l++; p=1;
        }

        int n = data.size();
        while(data.get(n-1) == nl) n--;

        byte[] byteArray = new byte[1 + n];
        for(int i=0; i<n; i++) byteArray[i]= data.get(i); byteArray[n] = nl;
        FileOutputStream fos = new FileOutputStream(f); fos.write(byteArray); fos.close();
        System.out.println(data.size() + " bytes written to file " + f + "\n\n");
    }

    private static void processMD(String f) throws IOException
    {
        System.out.println("Process MD File: " + f);

        Path path = Paths.get(fileName);
        String content = Files.readString(path, StandardCharsets.UTF_8);

        content = content.replace("\r", "");
        content = content.replace((char) 8211, '-');
        content = content.replace((char) 8212, '-');
        content = content.replaceAll("(?m)[ \\t]+$", "");   // trailing whitespace on each line
        content = content.replaceAll("\\n{2,}\\z", "\n");   // many blank lines at end -> one newline

        Files.writeString(path, content, StandardCharsets.UTF_8);
    }

}
